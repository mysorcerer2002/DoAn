"""Smoke test Phase 9 — voucher claim v2.2 guards.

Kịch bản:
A. claim OK trên campaign approved → voucher có issuance_id,
   issue_source='manual', discount_snapshot (+ terms_hash), lazy issuance row.
B. claim 2 lần cùng member → AlreadyClaimedError (409).
C. claim trên campaign pending_approval → CampaignNotEligibleError.
D. claim trên campaign authorization.revoked → CampaignNotEligibleError.
E. claim với max_issuances=1 sau khi đã đầy → CampaignFullError.
"""

import asyncio
import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.core.db import AsyncSessionLocal
from app.models.campaign import Campaign
from app.models.campaign_issuance import CampaignIssuance
from app.models.membership import Membership
from app.models.tenant import Tenant
from app.models.tenant_authorization import TenantAuthorization
from app.models.user import User
from app.services.voucher_service import (
    AlreadyClaimedError,
    CampaignFullError,
    CampaignNotEligibleError,
    VoucherService,
)


async def _mk_campaign(
    db, *, tenant_id: int, owner_id: int,
    approval_status: str = "auto_approved",
    max_issuances: int | None = None,
    with_auth: bool = False,
    auth_revoked: bool = False,
    terms: str | None = "Điều khoản mẫu smoke",
) -> tuple[Campaign, int | None]:
    now = datetime.now(timezone.utc)
    c = Campaign(
        tenant_id=tenant_id,
        name=f"P9 smoke {int(now.timestamp()*1000) % 10_000_000}",
        description="Phase 9 smoke",
        terms=terms,
        discount_type="percent",
        discount_value=15,
        min_order=0,
        max_issuances=max_issuances,
        starts_at=now - timedelta(hours=1),
        ends_at=now + timedelta(days=7),
        is_active=True,
        source="manual",
        program_form="giam_gia",
        approval_status=approval_status,
        approval_tier="none",
        estimated_cost=0,
        realized_cost=0,
        created_by_user_id=owner_id,
    )
    db.add(c)
    await db.flush()

    auth_id: int | None = None
    if with_auth:
        auth = TenantAuthorization(
            tenant_id=tenant_id,
            scope="per_campaign",
            campaign_id=c.id,
            document_content_hash=f"hash_p9_{int(now.timestamp()*1000000)}",
            signed_by_user_id=owner_id,
            signed_at=now,
            signature_method="otp_email",
            signature_payload={"ip": "127.0.0.1", "otp_purpose": "sign_authorization"},
            valid_from=now,
            valid_until=now + timedelta(days=365),
            retention_until=now + timedelta(days=365 * 10 + 5),
            revoked_at=now if auth_revoked else None,
        )
        db.add(auth)
        await db.flush()
        auth_id = auth.id
        c.authorization_id = auth_id
        await db.flush()
    return c, auth_id


async def _pick_membership(db, tenant_id: int) -> Membership:
    m = await db.scalar(
        select(Membership).where(Membership.tenant_id == tenant_id).limit(1)
    )
    assert m is not None, "cần membership sẵn có"
    return m


async def main() -> None:
    async with AsyncSessionLocal() as db:
        tenant = await db.scalar(select(Tenant).where(Tenant.id > 0).limit(1))
        owner = await db.scalar(select(User).where(User.system_role == "regular").limit(1))
        assert tenant and owner, "cần tenant + user seed"
        tenant_id = tenant.id
        owner_id = owner.id
        print(f"tenant={tenant_id} owner={owner_id}")

        svc = VoucherService(db)
        m = await _pick_membership(db, tenant_id)
        member_id = m.id

        # ── Scenario A: claim OK ───────────────────────────────────────
        c_a, _ = await _mk_campaign(db, tenant_id=tenant_id, owner_id=owner_id)
        await db.commit()
        v = await svc.claim(
            tenant_id=tenant_id, membership_id=member_id, campaign_id=c_a.id,
        )
        await db.commit()
        assert v.issuance_id is not None, f"voucher phải có issuance_id: {v}"
        assert v.issue_source == "manual", v.issue_source
        snap = v.discount_snapshot
        expect_terms = hashlib.sha256(c_a.terms.encode("utf-8")).hexdigest()
        assert snap["discount_type"] == "percent", snap
        assert snap["discount_value"] == 15, snap
        assert snap["terms_hash"] == expect_terms, (snap, expect_terms)
        # Issuance row lazy-create name IS NULL, issue_mode=manual.
        issuance = await db.get(CampaignIssuance, v.issuance_id)
        assert issuance and issuance.name is None and issuance.issue_mode == "manual"
        assert issuance.issued_count == 1
        print(f"[A] claim OK — voucher #{v.id} issuance #{v.issuance_id} snapshot={snap}")

        # ── Scenario B: claim lại → AlreadyClaimed ──────────────────────
        try:
            await svc.claim(
                tenant_id=tenant_id, membership_id=member_id, campaign_id=c_a.id,
            )
            raise AssertionError("phải raise AlreadyClaimedError")
        except AlreadyClaimedError:
            print("[B] AlreadyClaimedError OK")
        await db.rollback()

        # ── Scenario C: pending_approval → NotEligible ─────────────────
        c_pending, _ = await _mk_campaign(
            db, tenant_id=tenant_id, owner_id=owner_id,
            approval_status="pending_approval",
        )
        await db.commit()
        try:
            await svc.claim(
                tenant_id=tenant_id, membership_id=member_id, campaign_id=c_pending.id,
            )
            raise AssertionError("phải raise CampaignNotEligibleError")
        except CampaignNotEligibleError as e:
            print(f"[C] pending → NotEligible OK ({e})")
        await db.rollback()

        # ── Scenario D: authorization.revoked_at → NotEligible ─────────
        c_rev, _ = await _mk_campaign(
            db, tenant_id=tenant_id, owner_id=owner_id,
            with_auth=True, auth_revoked=True,
        )
        await db.commit()
        try:
            await svc.claim(
                tenant_id=tenant_id, membership_id=member_id, campaign_id=c_rev.id,
            )
            raise AssertionError("phải raise CampaignNotEligibleError")
        except CampaignNotEligibleError as e:
            print(f"[D] authorization revoked → NotEligible OK ({e})")
        await db.rollback()

        # ── Scenario E: max_issuances đầy → CampaignFull ───────────────
        c_full, _ = await _mk_campaign(
            db, tenant_id=tenant_id, owner_id=owner_id, max_issuances=1,
        )
        await db.commit()
        # Pick 2 membership khác nhau để đầy
        ms = (await db.scalars(
            select(Membership).where(Membership.tenant_id == tenant_id).limit(2)
        )).all()
        assert len(ms) >= 2, "cần ≥ 2 membership để test full"
        await svc.claim(
            tenant_id=tenant_id, membership_id=ms[0].id, campaign_id=c_full.id,
        )
        await db.commit()
        try:
            await svc.claim(
                tenant_id=tenant_id, membership_id=ms[1].id, campaign_id=c_full.id,
            )
            raise AssertionError("phải raise CampaignFullError")
        except CampaignFullError as e:
            print(f"[E] max_issuances đầy → CampaignFull OK ({e})")
        await db.rollback()

        # ── Scenario F: lazy issuance reuse — claim lần 2 (member khác) ─
        ms2 = (await db.scalars(
            select(Membership).where(Membership.tenant_id == tenant_id).limit(2)
        )).all()
        if len(ms2) >= 2:
            c_f, _ = await _mk_campaign(db, tenant_id=tenant_id, owner_id=owner_id)
            await db.commit()
            v1 = await svc.claim(
                tenant_id=tenant_id, membership_id=ms2[0].id, campaign_id=c_f.id,
            )
            v2 = await svc.claim(
                tenant_id=tenant_id, membership_id=ms2[1].id, campaign_id=c_f.id,
            )
            await db.commit()
            assert v1.issuance_id == v2.issuance_id, (
                f"2 voucher cùng campaign phải reuse issuance_id: {v1.issuance_id} vs {v2.issuance_id}"
            )
            # issued_count của issuance = 2
            total = await db.scalar(
                select(func.count()).select_from(CampaignIssuance)
                .where(CampaignIssuance.campaign_id == c_f.id)
            )
            assert total == 1, f"chỉ được tạo 1 lazy issuance row, thấy {total}"
            print(f"[F] lazy issuance reuse OK — issuance #{v1.issuance_id} cho 2 vouchers")

        # ── Scenario G: snapshot isolation — edit campaign sau khi issue ─
        from app.services.transaction_service import TransactionService
        c_g, _ = await _mk_campaign(db, tenant_id=tenant_id, owner_id=owner_id)
        await db.commit()
        ms_g = (await db.scalars(
            select(Membership).where(Membership.tenant_id == tenant_id).limit(1)
        )).all()
        v_g = await svc.claim(
            tenant_id=tenant_id, membership_id=ms_g[0].id, campaign_id=c_g.id,
        )
        await db.commit()
        # Đổi campaign từ 15% → 5% sau khi voucher đã issue.
        c_g.discount_value = 5
        await db.flush()
        await db.commit()
        txn_svc = TransactionService(db)
        # Dùng private _apply_voucher_if_provided (integration mô phỏng POS).
        _voucher_id, discount = await txn_svc._apply_voucher_if_provided(
            tenant_id=tenant_id,
            voucher_code=v_g.code,
            membership_id=ms_g[0].id,
            gross_amount=100_000,
        )
        # Snapshot 15% → discount = 15000, không phải 5000 của live campaign.
        assert discount == 15_000, (
            f"discount phải đọc từ snapshot (15%=15000), actual={discount}"
        )
        await db.rollback()  # huỷ mark_used
        print(f"[G] snapshot isolation OK — discount={discount} (giữ 15% dù campaign đổi 5%)")

        print("\n✅ Phase 9 smoke PASS")


if __name__ == "__main__":
    asyncio.run(main())
