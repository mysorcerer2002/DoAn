"""Smoke test Phase 11 — jobs: expire_vouchers + overdue report + retention purge.

Kịch bản:
A. Voucher `status=issued, expires_at < NOW` → `expire_vouchers_job`
   chuyển status=expired.
B. Campaign `approval_status=approved, post_report_due_at < NOW,
   post_report_submitted_at IS NULL` → `check_post_report_overdue_job`
   log WARNING + trả về overdue_count >= 1.
C. `tenant_authorizations` signed_at=11y ago, retention_until=1y ago
   + `campaign_service_fees` created_at=11y ago, retention_until=1y ago
   → `purge_retention_job` hard-delete cả hai.

Rows test insert qua raw SQL để né CHECK constraint
`retention_until >= signed_at/created_at + INTERVAL '10 years'` — set
cả signed_at/created_at lùi >10 năm cho CHECK pass.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from io import StringIO

from sqlalchemy import select, text

from app.core.db import AsyncSessionLocal
from app.jobs.check_post_report_overdue import check_post_report_overdue_job
from app.jobs.expire_vouchers import expire_vouchers_job
from app.jobs.purge_retention import purge_retention_job
from app.models.campaign import Campaign
from app.models.campaign_service_fee import CampaignServiceFee
from app.models.membership import Membership
from app.models.tenant import Tenant
from app.models.tenant_authorization import TenantAuthorization
from app.models.user import User
from app.models.voucher import Voucher, VoucherStatus
from app.services.voucher_service import VoucherService


async def _mk_campaign(
    db, *, tenant_id: int, owner_id: int,
    approval_status: str = "auto_approved",
) -> Campaign:
    now = datetime.now(timezone.utc)
    c = Campaign(
        tenant_id=tenant_id,
        name=f"P11 {int(now.timestamp()*1000) % 10_000_000}",
        description="Phase 11 smoke",
        terms="Điều khoản mẫu",
        discount_type="percent",
        discount_value=10,
        min_order=0,
        starts_at=now - timedelta(hours=1),
        ends_at=now + timedelta(days=7),
        is_active=True,
        source="manual",
        program_form="giam_gia",
        approval_status=approval_status,
        approval_tier="none",
        estimated_cost=0,
        realized_cost=0,
        service_fee_total=0,
        service_fee_status="none",
        created_by_user_id=owner_id,
    )
    db.add(c)
    await db.flush()
    return c


async def main() -> None:
    async with AsyncSessionLocal() as db:
        tenant = await db.scalar(select(Tenant).where(Tenant.id > 0).limit(1))
        owner = await db.scalar(
            select(User).where(User.system_role == "regular").limit(1)
        )
        assert tenant and owner
        tenant_id, owner_id = tenant.id, owner.id
        m = await db.scalar(
            select(Membership).where(Membership.tenant_id == tenant_id).limit(1)
        )
        assert m is not None
        member_id = m.id

        # ── A: expire_vouchers ────────────────────────────────────────
        c_a = await _mk_campaign(db, tenant_id=tenant_id, owner_id=owner_id)
        await db.commit()
        c_a_id = c_a.id
        voucher_svc = VoucherService(db)
        v = await voucher_svc.claim(
            tenant_id=tenant_id, membership_id=member_id, campaign_id=c_a_id,
        )
        await db.commit()
        v_id = v.id
        # Lùi expires_at về quá khứ 1 giờ.
        await db.execute(
            text(
                "UPDATE vouchers SET expires_at = NOW() - INTERVAL '1 hour' "
                "WHERE id = :vid"
            ),
            {"vid": v_id},
        )
        await db.commit()

    result_a = await expire_vouchers_job()
    assert result_a.get("expired", 0) >= 1, f"phải expire ít nhất 1: {result_a}"

    async with AsyncSessionLocal() as db:
        v_after = await db.get(Voucher, v_id)
        assert v_after.status == VoucherStatus.EXPIRED, v_after.status
    print(f"[A] expire_vouchers OK — voucher #{v_id} → expired, count={result_a['expired']}")

    # ── B: check_post_report_overdue ──────────────────────────────────
    async with AsyncSessionLocal() as db:
        c_b = await _mk_campaign(
            db, tenant_id=tenant_id, owner_id=owner_id,
            approval_status="approved",
        )
        c_b.post_report_due_at = datetime.now(timezone.utc) - timedelta(days=5)
        c_b.post_report_submitted_at = None
        await db.flush()
        await db.commit()
        c_b_id = c_b.id

    # Capture warn log.
    logger = logging.getLogger("app.jobs.check_post_report_overdue")
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.WARNING)
    logger.addHandler(handler)
    try:
        result_b = await check_post_report_overdue_job()
    finally:
        logger.removeHandler(handler)

    assert result_b.get("overdue_count", 0) >= 1, result_b
    log_b = stream.getvalue()
    assert f"#{c_b_id}" in log_b, f"log phải chứa campaign id: {log_b!r}"
    print(f"[B] check_post_report_overdue OK — count={result_b['overdue_count']}, log captured")

    # ── C: purge_retention ────────────────────────────────────────────
    async with AsyncSessionLocal() as db:
        c_c = await _mk_campaign(db, tenant_id=tenant_id, owner_id=owner_id)
        await db.commit()
        c_c_id = c_c.id

        # INSERT authorization với signed_at=11 năm trước, retention_until=1 năm trước.
        auth_row = await db.execute(
            text(
                """
                INSERT INTO tenant_authorizations (
                    tenant_id, scope, campaign_id, document_content_hash,
                    signed_by_user_id, signed_at, signature_method,
                    signature_payload, valid_from, valid_until, retention_until,
                    created_at, updated_at
                ) VALUES (
                    :tid, 'per_campaign', :cid, :hash,
                    :uid, NOW() - INTERVAL '11 years', 'click_to_sign',
                    '{"ip":"127.0.0.1"}'::jsonb,
                    NOW() - INTERVAL '11 years',
                    NOW() - INTERVAL '10 years 11 months',
                    NOW() - INTERVAL '1 year',
                    NOW() - INTERVAL '11 years',
                    NOW() - INTERVAL '11 years'
                ) RETURNING id
                """
            ),
            {
                "tid": tenant_id,
                "cid": c_c_id,
                "hash": f"p11_auth_{int(datetime.now().timestamp())}",
                "uid": owner_id,
            },
        )
        auth_id = auth_row.scalar()

        # INSERT service fee với created_at=11 năm trước.
        fee_row = await db.execute(
            text(
                """
                INSERT INTO campaign_service_fees (
                    campaign_id, tenant_id, fee_type, amount, vat_rate,
                    description, status, retention_until,
                    created_by_user_id, created_at, updated_at
                ) VALUES (
                    :cid, :tid, 'so_ct_filing', 500000, 10.00,
                    'Phase 11 smoke fee', 'waived',
                    NOW() - INTERVAL '1 year',
                    :uid,
                    NOW() - INTERVAL '11 years',
                    NOW() - INTERVAL '11 years'
                ) RETURNING id
                """
            ),
            {"cid": c_c_id, "tid": tenant_id, "uid": owner_id},
        )
        fee_id = fee_row.scalar()
        await db.commit()

    result_c = await purge_retention_job()
    assert result_c.get("auth_deleted", 0) >= 1, f"phải xoá >=1 auth: {result_c}"
    assert result_c.get("fee_deleted", 0) >= 1, f"phải xoá >=1 fee: {result_c}"

    async with AsyncSessionLocal() as db:
        auth_check = await db.get(TenantAuthorization, auth_id)
        fee_check = await db.get(CampaignServiceFee, fee_id)
        assert auth_check is None, f"authorization #{auth_id} phải bị xoá"
        assert fee_check is None, f"fee #{fee_id} phải bị xoá"
    print(
        f"[C] purge_retention OK — auth_deleted={result_c['auth_deleted']}, "
        f"fee_deleted={result_c['fee_deleted']}"
    )

    print("\n✅ Phase 11 smoke PASS")


if __name__ == "__main__":
    asyncio.run(main())
