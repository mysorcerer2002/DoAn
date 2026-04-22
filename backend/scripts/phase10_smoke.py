"""Smoke test Phase 10 — legal_discount_ratio GENERATED + realized_cost view.

Kịch bản:
A. Transaction với voucher giảm 15% → legal_discount_ratio ≈ 15.00, KHÔNG warn.
B. Transaction với voucher fixed lớn (giảm 70%) → ratio > 50, HAS warn log.
C. Transaction không voucher → ratio IS NULL, không warn.
D. `get_campaign_realized_cost_from_view` đọc sum voucher_discount_amount.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from io import StringIO

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.models.campaign import Campaign
from app.models.membership import Membership
from app.models.tenant import Tenant
from app.models.transaction import Transaction, TransactionMethod
from app.models.user import User
from app.services.transaction_service import TransactionService
from app.services.voucher_service import VoucherService


async def _mk_campaign(
    db, *, tenant_id: int, owner_id: int,
    discount_type: str = "percent", discount_value: int = 15,
    max_discount: int | None = None,
) -> Campaign:
    now = datetime.now(timezone.utc)
    c = Campaign(
        tenant_id=tenant_id,
        name=f"P10 {int(now.timestamp()*1000) % 10_000_000}",
        description="Phase 10 smoke",
        terms="Điều khoản mẫu",
        discount_type=discount_type,
        discount_value=discount_value,
        max_discount=max_discount,
        min_order=0,
        max_issuances=None,
        starts_at=now - timedelta(hours=1),
        ends_at=now + timedelta(days=7),
        is_active=True,
        source="manual",
        program_form="giam_gia",
        approval_status="auto_approved",
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
    # Attach memory handler to capture warn logs.
    logger = logging.getLogger("app.services.transaction_service")
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.WARNING)
    logger.addHandler(handler)

    async with AsyncSessionLocal() as db:
        tenant = await db.scalar(select(Tenant).where(Tenant.id > 0).limit(1))
        owner = await db.scalar(select(User).where(User.system_role == "regular").limit(1))
        assert tenant and owner
        tenant_id, owner_id = tenant.id, owner.id
        m = await db.scalar(
            select(Membership).where(Membership.tenant_id == tenant_id).limit(1)
        )
        assert m is not None
        member_id = m.id
        staff = await db.scalar(select(User).where(User.id == owner_id).limit(1))
        staff_id = staff.id

        voucher_svc = VoucherService(db)
        txn_svc = TransactionService(db)

        # ── Scenario A: 15% voucher trên gross 100k → ratio 15.
        c_a = await _mk_campaign(db, tenant_id=tenant_id, owner_id=owner_id,
                                  discount_type="percent", discount_value=15)
        await db.commit()
        c_a_id = c_a.id
        v_a = await voucher_svc.claim(
            tenant_id=tenant_id, membership_id=member_id, campaign_id=c_a_id,
        )
        await db.commit()
        v_a_id = v_a.id
        stream.truncate(0); stream.seek(0)
        txn_a = Transaction(
            tenant_id=tenant_id, membership_id=member_id, staff_id=staff_id,
            gross_amount=100_000, voucher_id=v_a_id,
            voucher_discount_amount=15_000, net_amount=85_000,
            points_earned=0, method=TransactionMethod.MANUAL,
        )
        db.add(txn_a)
        await db.flush()
        await db.refresh(txn_a, ["legal_discount_ratio"])
        ratio_a = txn_a.legal_discount_ratio
        await txn_svc._warn_if_high_discount_ratio(txn_a)
        assert ratio_a is not None and float(ratio_a) == 15.00, ratio_a
        log_a = stream.getvalue()
        assert "vượt ngưỡng" not in log_a, f"không được warn: {log_a!r}"
        print(f"[A] ratio=15% OK — legal_discount_ratio={ratio_a}, no warn")

        # ── Scenario B: discount 70k trên gross 100k → ratio 70 → warn.
        # Reuse voucher A (chỉ test ratio từ fields transaction, không validate voucher).
        stream.truncate(0); stream.seek(0)
        txn_b = Transaction(
            tenant_id=tenant_id, membership_id=member_id, staff_id=staff_id,
            gross_amount=100_000, voucher_id=v_a_id,
            voucher_discount_amount=70_000, net_amount=30_000,
            points_earned=0, method=TransactionMethod.MANUAL,
        )
        db.add(txn_b)
        await db.flush()
        await db.refresh(txn_b, ["legal_discount_ratio"])
        ratio_b = txn_b.legal_discount_ratio
        await txn_svc._warn_if_high_discount_ratio(txn_b)
        assert float(ratio_b) == 70.00, ratio_b
        log_b = stream.getvalue()
        assert "vượt ngưỡng NĐ 81 Đ7" in log_b, f"phải warn: {log_b!r}"
        print(f"[B] ratio=70% OK — warn log captured")

        # ── Scenario C: no voucher → ratio NULL, no warn.
        stream.truncate(0); stream.seek(0)
        txn_c = Transaction(
            tenant_id=tenant_id, membership_id=member_id, staff_id=staff_id,
            gross_amount=50_000, voucher_id=None,
            voucher_discount_amount=None, net_amount=50_000,
            points_earned=0, method=TransactionMethod.MANUAL,
        )
        db.add(txn_c)
        await db.flush()
        await db.refresh(txn_c, ["legal_discount_ratio"])
        ratio_c = txn_c.legal_discount_ratio
        await txn_svc._warn_if_high_discount_ratio(txn_c)
        assert ratio_c is None, ratio_c
        assert "vượt ngưỡng" not in stream.getvalue()
        print(f"[C] no voucher OK — ratio IS NULL, no warn")
        await db.rollback()

        # ── Scenario D: realized_cost từ view.
        c_d = await _mk_campaign(db, tenant_id=tenant_id, owner_id=owner_id,
                                  discount_type="percent", discount_value=10)
        await db.commit()
        c_d_id = c_d.id
        v_d = await voucher_svc.claim(
            tenant_id=tenant_id, membership_id=member_id, campaign_id=c_d_id,
        )
        v_d_id = v_d.id
        await db.commit()
        await voucher_svc.mark_used(tenant_id=tenant_id, voucher_id=v_d_id)
        txn_d = Transaction(
            tenant_id=tenant_id, membership_id=member_id, staff_id=staff_id,
            gross_amount=200_000, voucher_id=v_d_id,
            voucher_discount_amount=20_000, net_amount=180_000,
            points_earned=0, method=TransactionMethod.MANUAL,
        )
        db.add(txn_d)
        await db.commit()
        realized = await txn_svc.get_campaign_realized_cost_from_view(c_d_id)
        assert realized == 20_000, f"realized_cost từ view phải = 20000, actual={realized}"
        print(f"[D] realized_cost view OK — campaign #{c_d_id} realized={realized}")

        print("\n✅ Phase 10 smoke PASS")


if __name__ == "__main__":
    asyncio.run(main())
