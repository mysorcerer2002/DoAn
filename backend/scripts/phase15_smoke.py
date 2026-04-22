"""Smoke test Phase 15 — E2E lifecycle voucher system rebuild v2.2.

Kịch bản:
  A. Enroll auto-approve (tier=none): template giam_gia cost thấp, sign →
     campaign.approval_status='auto_approved', authorization.id set.
  B. Enroll pending OTP (tier=notify_so_ct): cost > auto threshold, sign →
     campaign.approval_status='pending_approval', fees estimated.
  C. Ops flow + approve (campaign B):
     mark_ops_started → add xac_nhan_so_ct → approve → status='approved'.
  D. Claim voucher → mark_used → reject ack=False raise → ack=True OK, trả
     (cancelled_count, used_count=1).
  E. Revoke authorization:
     E1 — pending chưa ops_started → revoke OK (revoked_at set).
     E2 — pending + ops_started → RevokeBlockedOpsStartedError.
  F. Concurrent enroll cùng template + tenant: 2nd sign → EnrollmentError
     (partial unique uq_campaigns_tenant_template_active_pending).

Script insert 3 template mới (p15_*) để tránh đụng seed. Tenant/owner/membership
lấy từ seed sẵn có. OTP giả lập bằng cách đọc raw code từ
VerificationCodeService.create_code (không qua email thật).
"""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text

from app.core.db import AsyncSessionLocal
from app.models.campaign_template import CampaignTemplate
from app.models.membership import Membership
from app.models.tenant import Tenant
from app.models.user import User
from app.models.verification_code import VerificationCodePurpose
from app.models.voucher import Voucher, VoucherStatus
from app.schemas.campaign_enrollment import EnrollFormInput
from app.services.campaign_approval_service import (
    CampaignApprovalService,
    UsedVouchersBlockRejectError,
)
from app.services.campaign_enrollment_service import (
    CampaignEnrollmentService,
    EnrollmentError,
    form_commitment,
)
from app.services.tenant_authorization_service import (
    RevokeBlockedOpsStartedError,
    TenantAuthorizationService,
)
from app.services.verification_code_service import VerificationCodeService
from app.services.voucher_service import VoucherService


TAG = f"p15_{int(datetime.now().timestamp())}"


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════


async def _seed_templates(db) -> dict[str, int]:
    """Insert 3 template fixed giam_gia, trả {key: template_id}."""
    rows = [
        # A: cost = 10k × 10 = 100k → tier=none (auto)
        ("A", f"{TAG}-auto", "P15 Auto", 10_000, 10),
        # B: cost = 10k × 100 = 1M → tier=notify_so_ct (pending)
        ("B", f"{TAG}-notify", "P15 Notify", 10_000, 100),
    ]
    out: dict[str, int] = {}
    for key, code, name, disc, maxi in rows:
        tpl = CampaignTemplate(
            code=code,
            name=name,
            description="Phase 15 smoke",
            source="manual",
            program_form="giam_gia",
            discount_type="fixed",
            min_order_floor=0,
            max_discount_fixed_cap=disc * 2,
            max_issuances_cap=maxi * 2,
            is_active=True,
            version=1,
        )
        db.add(tpl)
        await db.flush()
        out[key] = tpl.id
    return out


def _mk_form(
    *, template_id: int, name_suffix: str, discount: int, issuances: int
) -> EnrollFormInput:
    now = datetime.now(timezone.utc)
    return EnrollFormInput(
        template_id=template_id,
        name=f"{TAG} {name_suffix}",
        description="Smoke enroll form",
        terms="Điều khoản mẫu",
        usage_guide="Áp dụng toàn menu",
        support_contact="owner@example.vn",
        discount_value=discount,
        min_order=0,
        max_discount=None,
        max_issuances=issuances,
        starts_at=now - timedelta(minutes=5),
        ends_at=now + timedelta(days=7),
    )


async def _sign(
    db, *, tenant_id: int, user_id: int, form: EnrollFormInput
):
    """Tạo OTP + gọi sign_and_enroll. Commit sau khi thành công."""
    vc = VerificationCodeService(db)
    code = await vc.create_code(
        user_id=user_id,
        purpose=VerificationCodePurpose.AUTHORIZATION_SIGN,
        context_hash=form_commitment(form),
    )
    await db.commit()

    svc = CampaignEnrollmentService(db)
    res = await svc.sign_and_enroll(
        tenant_id=tenant_id,
        user_id=user_id,
        form=form,
        client_ip="127.0.0.1",
        user_agent="phase15-smoke",
        otp_code=code,
        consent_checked=True,
    )
    await db.commit()
    return res


async def _sign_expect_fail(
    db, *, tenant_id: int, user_id: int, form: EnrollFormInput
):
    """Giả lập OTP + sign nhưng không rollback — caller bắt exception."""
    vc = VerificationCodeService(db)
    code = await vc.create_code(
        user_id=user_id,
        purpose=VerificationCodePurpose.AUTHORIZATION_SIGN,
        context_hash=form_commitment(form),
    )
    await db.commit()

    svc = CampaignEnrollmentService(db)
    await svc.sign_and_enroll(
        tenant_id=tenant_id,
        user_id=user_id,
        form=form,
        client_ip="127.0.0.1",
        user_agent="phase15-smoke",
        otp_code=code,
        consent_checked=True,
    )


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════


async def main() -> None:
    async with AsyncSessionLocal() as db:
        tenant = await db.scalar(select(Tenant).where(Tenant.id > 0).limit(1))
        owner = await db.scalar(
            select(User).where(User.system_role == "regular").limit(1)
        )
        assert tenant and owner, "Cần seed tenant + owner trước"
        tenant_id, owner_id = tenant.id, owner.id

        member = await db.scalar(
            select(Membership).where(Membership.tenant_id == tenant_id).limit(1)
        )
        assert member, "Cần seed membership"
        membership_id = member.id

        templates = await _seed_templates(db)
        await db.commit()

    print(f"[setup] tenant={tenant_id} owner={owner_id} templates={templates}")

    # ── A: enroll auto-approve ────────────────────────────────────────
    async with AsyncSessionLocal() as db:
        form_a = _mk_form(
            template_id=templates["A"],
            name_suffix="auto",
            discount=10_000,
            issuances=10,
        )
        preview_a = await CampaignEnrollmentService(db).preview(
            tenant_id=tenant_id, user_id=owner_id, form=form_a
        )
        assert preview_a.approval_tier == "none", preview_a.approval_tier
        assert preview_a.estimated_cost == 100_000, preview_a.estimated_cost

        res_a = await _sign(db, tenant_id=tenant_id, user_id=owner_id, form=form_a)
        assert res_a.approval_status == "auto_approved", res_a
        assert res_a.approval_tier == "none"
        campaign_a_id = res_a.campaign_id
    print(f"[A] auto-approve OK — campaign #{campaign_a_id}, tier=none")

    # ── B: enroll pending notify_so_ct ────────────────────────────────
    async with AsyncSessionLocal() as db:
        form_b = _mk_form(
            template_id=templates["B"],
            name_suffix="notify",
            discount=10_000,
            issuances=100,
        )
        preview_b = await CampaignEnrollmentService(db).preview(
            tenant_id=tenant_id, user_id=owner_id, form=form_b
        )
        assert preview_b.approval_tier == "notify_so_ct", preview_b.approval_tier
        assert preview_b.estimated_cost == 1_000_000, preview_b.estimated_cost

        res_b = await _sign(db, tenant_id=tenant_id, user_id=owner_id, form=form_b)
        assert res_b.approval_status == "pending_approval", res_b
        campaign_b_id = res_b.campaign_id
    print(
        f"[B] pending_approval OK — campaign #{campaign_b_id}, "
        f"tier=notify_so_ct, fee={preview_b.fee_total_with_vat}"
    )

    # ── C: ops flow + approve campaign B ──────────────────────────────
    async with AsyncSessionLocal() as db:
        svc = CampaignApprovalService(db)
        await svc.mark_ops_started(campaign_id=campaign_b_id, user_id=owner_id)
        await svc.add_regulatory_submission(
            campaign_id=campaign_b_id,
            doc_type="xac_nhan_so_ct",
            reference_no=f"{TAG}-ref",
            url=None,
            note="Smoke test",
            submitted_at=None,
            user_id=owner_id,
        )
        approved = await svc.approve(campaign_id=campaign_b_id, user_id=owner_id)
        await db.commit()
        assert approved.approval_status == "approved", approved.approval_status
    print(f"[C] approve OK — campaign #{campaign_b_id} → approved")

    # ── D: claim + used voucher + reject with ack gate ────────────────
    async with AsyncSessionLocal() as db:
        voucher = await VoucherService(db).claim(
            tenant_id=tenant_id,
            membership_id=membership_id,
            campaign_id=campaign_b_id,
        )
        await db.commit()
        voucher_id = voucher.id

        used = await VoucherService(db).mark_used(
            tenant_id=tenant_id, voucher_id=voucher_id
        )
        await db.commit()
        assert used.status == VoucherStatus.USED, used.status

    # D1: reject ack=False → raise
    async with AsyncSessionLocal() as db:
        try:
            await CampaignApprovalService(db).reject(
                campaign_id=campaign_b_id,
                user_id=owner_id,
                reason="Smoke reject without ack",
                acknowledge_used_vouchers=False,
            )
            raise AssertionError("reject ack=False phải raise")
        except UsedVouchersBlockRejectError as e:
            assert "1" in str(e) or hasattr(e, "used_count"), e
            print(f"[D1] reject ack=False → blocked ({e})")
        await db.rollback()

    # D2: reject ack=True → OK, cancelled=0 (chỉ có 1 voucher used, không issued)
    async with AsyncSessionLocal() as db:
        campaign, cancelled, used_count = await CampaignApprovalService(db).reject(
            campaign_id=campaign_b_id,
            user_id=owner_id,
            reason="Smoke reject with ack",
            acknowledge_used_vouchers=True,
        )
        await db.commit()
        assert campaign.approval_status == "rejected", campaign.approval_status
        assert used_count == 1, f"phải giữ 1 voucher used: {used_count}"
        assert cancelled == 0, f"không còn voucher issued để cancel: {cancelled}"

        v_after = await db.get(Voucher, voucher_id)
        assert v_after.status == VoucherStatus.USED, (
            "voucher used KHÔNG bị đụng khi reject"
        )
    print(
        f"[D2] reject ack=True OK — cancelled={cancelled}, used_kept={used_count}"
    )

    # ── E: revoke authorization ───────────────────────────────────────
    # E1: enroll pending mới → revoke trước ops_start → OK
    async with AsyncSessionLocal() as db:
        form_e1 = _mk_form(
            template_id=templates["B"],
            name_suffix="revoke-ok",
            discount=10_000,
            issuances=100,
        )
        res_e1 = await _sign(
            db, tenant_id=tenant_id, user_id=owner_id, form=form_e1
        )
        campaign_e1_id = res_e1.campaign_id
        auth_e1_id = res_e1.authorization_id

    async with AsyncSessionLocal() as db:
        auth = await TenantAuthorizationService(db).revoke(
            tenant_id=tenant_id,
            auth_id=auth_e1_id,
            user_id=owner_id,
            reason="smoke revoke before ops",
        )
        await db.commit()
        assert auth.revoked_at is not None, "revoked_at phải set"

        # Reject campaign E1 ngay để không chặn partial unique cho E2/F.
        await CampaignApprovalService(db).reject(
            campaign_id=campaign_e1_id,
            user_id=owner_id,
            reason="smoke cleanup sau revoke",
            acknowledge_used_vouchers=True,
        )
        await db.commit()
    print(f"[E1] revoke OK — auth #{auth_e1_id} (campaign #{campaign_e1_id})")

    # E2: enroll pending + ops_started → revoke → RevokeBlockedOpsStartedError
    async with AsyncSessionLocal() as db:
        form_e2 = _mk_form(
            template_id=templates["B"],
            name_suffix="revoke-blocked",
            discount=10_000,
            issuances=100,
        )
        res_e2 = await _sign(
            db, tenant_id=tenant_id, user_id=owner_id, form=form_e2
        )
        campaign_e2_id = res_e2.campaign_id
        auth_e2_id = res_e2.authorization_id

    async with AsyncSessionLocal() as db:
        await CampaignApprovalService(db).mark_ops_started(
            campaign_id=campaign_e2_id, user_id=owner_id
        )
        await db.commit()

    async with AsyncSessionLocal() as db:
        try:
            await TenantAuthorizationService(db).revoke(
                tenant_id=tenant_id,
                auth_id=auth_e2_id,
                user_id=owner_id,
                reason="smoke revoke after ops",
            )
            raise AssertionError("revoke sau ops_start phải raise")
        except RevokeBlockedOpsStartedError as e:
            print(f"[E2] revoke blocked OK — {e}")
        await db.rollback()

    # Cleanup E2 — reject để giải phóng partial unique cho scenario F.
    async with AsyncSessionLocal() as db:
        await CampaignApprovalService(db).reject(
            campaign_id=campaign_e2_id,
            user_id=owner_id,
            reason="smoke cleanup sau revoke-blocked",
            acknowledge_used_vouchers=True,
        )
        await db.commit()

    # ── F: concurrent enroll block (partial unique) ───────────────────
    # Template B tier=notify → pending_approval → partial unique áp dụng.
    # Lần 1 OK → lần 2 cùng template + tenant phải raise EnrollmentError.
    async with AsyncSessionLocal() as db:
        form_f1 = _mk_form(
            template_id=templates["B"],
            name_suffix="concurrent-first",
            discount=10_000,
            issuances=100,
        )
        res_f1 = await _sign(
            db, tenant_id=tenant_id, user_id=owner_id, form=form_f1
        )
        assert res_f1.approval_status == "pending_approval", res_f1

    async with AsyncSessionLocal() as db:
        form_f2 = _mk_form(
            template_id=templates["B"],
            name_suffix="concurrent-second",
            discount=10_000,
            issuances=100,
        )
        try:
            await _sign_expect_fail(
                db, tenant_id=tenant_id, user_id=owner_id, form=form_f2
            )
            raise AssertionError(
                "Enroll thứ 2 cùng template + tenant khi pending exists phải raise"
            )
        except EnrollmentError as e:
            msg = str(e)
            assert "pending" in msg.lower(), msg
            print(f"[F] concurrent block OK — {e}")
        await db.rollback()

    print("\n✅ Phase 15 smoke PASS")


if __name__ == "__main__":
    asyncio.run(main())
