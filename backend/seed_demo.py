"""Seed data phong phú cho demo + test.

Tạo 2 tenant độc lập (Cafe Cộng + Trà Sữa Lala) với đầy đủ:
- tier, point_rule, reward, campaign
- 5 customer/tenant + membership với tier đa dạng
- 14 ngày transactions (~30 txn/tenant)
- point_ledger entries (earn + adjust + redeem)
- voucher claims từ campaign
- redemption records từ reward

Dùng để test mọi endpoint có data + verify multi-tenant isolation.
"""

import asyncio
import random
import secrets
import string
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.core.security import hash_password
from app.models.campaign import Campaign, DiscountType
from app.models.membership import Membership
from app.models.point_ledger import LedgerReason, LedgerRefType, PointLedger
from app.models.point_rule import PointRule
from app.models.redemption import Redemption, RedemptionStatus
from app.models.reward import Reward
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.tier import Tier
from app.models.transaction import Transaction, TransactionMethod
from app.models.user import User
from app.models.voucher import Voucher, VoucherStatus


def _rand_code(n: int = 8) -> str:
    return "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(n))


async def _get_or_create_user(
    db, *, email: str, password: str, full_name: str, phone: str | None = None,
    system_role: str = "regular",
) -> User:
    user = await db.scalar(select(User).where(User.email == email))
    if user is not None:
        return user
    user = User(
        email=email,
        phone=phone,
        password_hash=hash_password(password),
        full_name=full_name,
        is_active=True,
        system_role=system_role,
        password_changed_at=datetime.now(UTC),
    )
    db.add(user)
    await db.flush()
    print(f"  ✓ User {email} ({system_role}, {password})")
    return user


async def _seed_tenant(
    db,
    *,
    name: str,
    slug: str,
    owner: User,
    description: str,
    tier_names: list[tuple[str, int]],
    rewards: list[tuple[str, int, int | None]],
    campaigns: list[tuple[str, int, int]],  # (name, discount_percent, max_discount)
    customers: list[tuple[str, str, str, int, str]],  # (email, name, phone, points, tier_name)
) -> dict:
    """Seed 1 tenant đầy đủ. Trả về dict với các id cần thiết."""
    tenant = await db.scalar(select(Tenant).where(Tenant.slug == slug))
    if tenant is None:
        tenant = Tenant(
            name=name,
            slug=slug,
            owner_user_id=owner.id,
            status=TenantStatus.ACTIVE,
            description=description,
            settings={
                "points_on_gross": False,
                "signup_bonus_points": 100,
                "voucher_default_ttl_days": 14,
                "redemption_default_ttl_days": 14,
            },
            activated_at=datetime.now(UTC),
        )
        db.add(tenant)
        await db.flush()
        db.add(TenantStaff(tenant_id=tenant.id, user_id=owner.id, role=TenantStaffRole.OWNER))
        await db.flush()
        print(f"✓ Tenant: {name} (id={tenant.id})")
    else:
        print(f"- Tenant đã tồn tại: {name}")

    # Point rule
    rule = await db.scalar(
        select(PointRule).where(PointRule.tenant_id == tenant.id, PointRule.is_active.is_(True))
    )
    if rule is None:
        db.add(PointRule(
            tenant_id=tenant.id,
            unit_amount=10_000,
            points_per_unit=Decimal("1"),
            min_amount=0,
            is_active=True,
        ))
        await db.flush()
        print("  ✓ Point rule: 10.000₫ = 1 điểm")

    # Tiers
    existing_tiers = (
        await db.scalars(
            select(Tier).where(Tier.tenant_id == tenant.id, Tier.deleted_at.is_(None))
        )
    ).all()
    if not existing_tiers:
        for tier_name, min_pts in tier_names:
            db.add(Tier(tenant_id=tenant.id, name=tier_name, min_points=min_pts, is_active=True))
        await db.flush()
        print(f"  ✓ {len(tier_names)} tiers")

    tiers_map = {
        t.name: t
        for t in (
            await db.scalars(
                select(Tier).where(Tier.tenant_id == tenant.id, Tier.deleted_at.is_(None))
            )
        ).all()
    }

    # Rewards
    existing_rewards = (
        await db.scalars(
            select(Reward).where(Reward.tenant_id == tenant.id, Reward.deleted_at.is_(None))
        )
    ).all()
    if not existing_rewards:
        for r_name, pts, stock in rewards:
            db.add(Reward(
                tenant_id=tenant.id,
                name=r_name,
                description=f"Đổi điểm lấy {r_name.lower()}",
                points_cost=pts,
                stock=stock,
                is_active=True,
            ))
        await db.flush()
        print(f"  ✓ {len(rewards)} rewards")

    rewards_list = (
        await db.scalars(
            select(Reward).where(Reward.tenant_id == tenant.id, Reward.deleted_at.is_(None))
        )
    ).all()

    # Campaigns
    now = datetime.now(UTC)
    existing_campaigns = (
        await db.scalars(select(Campaign).where(Campaign.tenant_id == tenant.id))
    ).all()
    if not existing_campaigns:
        for c_name, discount, max_disc in campaigns:
            db.add(Campaign(
                tenant_id=tenant.id,
                name=c_name,
                description=f"Khuyến mãi {c_name}",
                source="manual",
                discount_type=DiscountType.PERCENT,
                discount_value=discount,
                max_discount=max_disc,
                min_order=50_000,
                starts_at=now - timedelta(days=2),
                ends_at=now + timedelta(days=30),
                max_issuances=1000,
                is_active=True,
            ))
        await db.flush()
        print(f"  ✓ {len(campaigns)} campaigns")

    campaigns_list = (
        await db.scalars(select(Campaign).where(Campaign.tenant_id == tenant.id))
    ).all()

    # Customers + memberships
    memberships: list[Membership] = []
    for email, c_name, phone, points, tier_name in customers:
        user = await _get_or_create_user(
            db, email=email, password="khach1234", full_name=c_name, phone=phone,
        )
        membership = await db.scalar(
            select(Membership).where(
                Membership.tenant_id == tenant.id, Membership.user_id == user.id
            )
        )
        if membership is None:
            tier = tiers_map.get(tier_name)
            membership = Membership(
                tenant_id=tenant.id,
                user_id=user.id,
                current_tier_id=tier.id if tier else None,
                points_balance=points,
                total_points_earned=points,
                last_activity_at=datetime.now(UTC),
            )
            db.add(membership)
            await db.flush()
            print(f"  ✓ Membership {email} — {tier_name}, {points} điểm")
        memberships.append(membership)

    return {
        "tenant": tenant,
        "owner": owner,
        "tiers": tiers_map,
        "rewards": rewards_list,
        "campaigns": campaigns_list,
        "memberships": memberships,
    }


async def _seed_transactions_and_ledger(
    db, *, tenant: Tenant, owner: User, memberships: list[Membership], count: int = 30
) -> None:
    """Rải transactions đều trong 14 ngày gần nhất + ghi ledger entries."""
    existing = await db.scalar(
        select(Transaction.id).where(Transaction.tenant_id == tenant.id).limit(1)
    )
    if existing is not None:
        return

    rng = random.Random(42 + tenant.id)  # Deterministic
    now = datetime.now(UTC)
    for i in range(count):
        membership = rng.choice(memberships)
        days_ago = rng.randint(0, 13)
        hours_ago = rng.randint(0, 23)
        created_at = now - timedelta(days=days_ago, hours=hours_ago)
        gross = rng.choice([45_000, 65_000, 85_000, 120_000, 150_000, 180_000, 250_000])
        points_earned = gross // 10_000

        txn = Transaction(
            tenant_id=tenant.id,
            membership_id=membership.id,
            staff_id=owner.id,
            gross_amount=gross,
            net_amount=gross,
            points_earned=points_earned,
            method=TransactionMethod.QR_CUSTOMER,
            note=f"Giao dịch #{i + 1}",
        )
        txn.created_at = created_at
        db.add(txn)
        await db.flush()

        # Ledger entry earn
        new_balance = membership.points_balance + points_earned
        db.add(PointLedger(
            tenant_id=tenant.id,
            membership_id=membership.id,
            delta=points_earned,
            reason=LedgerReason.EARN,
            ref_type=LedgerRefType.TRANSACTION,
            ref_id=txn.id,
            balance_after=new_balance,
            description=f"Tích điểm từ giao dịch #{txn.id}",
        ))
        membership.points_balance = new_balance
        membership.total_points_earned += points_earned
        membership.last_activity_at = created_at

    await db.flush()
    print(f"  ✓ {count} transactions + ledger entries (14 ngày)")


async def _seed_redemptions(
    db, *, tenant: Tenant, memberships: list[Membership], rewards: list[Reward]
) -> None:
    """Mỗi customer đổi 1 reward từ kho."""
    if not rewards:
        return
    existing = await db.scalar(
        select(Redemption.id).where(Redemption.tenant_id == tenant.id).limit(1)
    )
    if existing is not None:
        return

    now = datetime.now(UTC)
    for i, membership in enumerate(memberships[:3]):
        reward = rewards[i % len(rewards)]
        if membership.points_balance < reward.points_cost:
            continue
        redemption = Redemption(
            tenant_id=tenant.id,
            membership_id=membership.id,
            reward_id=reward.id,
            points_spent=reward.points_cost,
            redemption_code=_rand_code(),
            status=RedemptionStatus.PENDING,
            redeemed_at=now - timedelta(days=i),
            expires_at=now + timedelta(days=14),
        )
        db.add(redemption)
        await db.flush()

        new_balance = membership.points_balance - reward.points_cost
        db.add(PointLedger(
            tenant_id=tenant.id,
            membership_id=membership.id,
            delta=-reward.points_cost,
            reason=LedgerReason.REDEEM,
            ref_type=LedgerRefType.REDEMPTION,
            ref_id=redemption.id,
            balance_after=new_balance,
            description=f"Đổi quà: {reward.name}",
        ))
        membership.points_balance = new_balance

        if reward.stock is not None:
            reward.stock = max(0, reward.stock - 1)

    await db.flush()
    print(f"  ✓ 3 redemptions + ledger entries")


async def _seed_vouchers(
    db, *, tenant: Tenant, memberships: list[Membership], campaigns: list[Campaign]
) -> None:
    """Phát voucher từ campaign cho 2 customer đầu."""
    if not campaigns:
        return
    existing = await db.scalar(
        select(Voucher.id).where(Voucher.tenant_id == tenant.id).limit(1)
    )
    if existing is not None:
        return

    now = datetime.now(UTC)
    campaign = campaigns[0]
    for i, membership in enumerate(memberships[:2]):
        voucher = Voucher(
            tenant_id=tenant.id,
            campaign_id=campaign.id,
            membership_id=membership.id,
            code=_rand_code(),
            status=VoucherStatus.ISSUED,
            issued_at=now - timedelta(days=i + 1),
            expires_at=now + timedelta(days=14),
        )
        db.add(voucher)

    await db.flush()
    print(f"  ✓ 2 vouchers phát hành")


async def main() -> None:
    async with AsyncSessionLocal() as db:
        print("=" * 50)
        print("SEED DATA — LOYALTY PLATFORM")
        print("=" * 50)

        # ===== Super Admin =====
        print("\n[1] Super Admin")
        await _get_or_create_user(
            db,
            email="admin@loyalty.vn",
            password="admin1234",
            full_name="Super Admin",
            system_role="super_admin",
        )

        # ===== Tenant 1: Cafe Cộng =====
        print("\n[2] Tenant 1 — Cafe Cộng - Bà Triệu")
        owner1 = await _get_or_create_user(
            db,
            email="owner@cafe.vn",
            password="owner1234",
            full_name="Lê Văn Bình",
            phone="0912345001",
        )
        ctx1 = await _seed_tenant(
            db,
            name="Cafe Cộng - Bà Triệu",
            slug="cafe-cong",
            owner=owner1,
            description="Quán cafe phong cách Việt Nam",
            tier_names=[
                ("Hạng Đồng", 0),
                ("Hạng Bạc", 500),
                ("Hạng Vàng", 2000),
                ("Hạng Bạch Kim", 5000),
            ],
            rewards=[
                ("Cafe Latte size M Free", 150, 50),
                ("Bánh ngọt cao cấp", 200, 30),
                ("Voucher giảm 50K", 500, None),
            ],
            campaigns=[("Giảm 20% Coffee", 20, 50_000)],
            customers=[
                ("khach1@gmail.com", "Nguyễn Thị Hoa", "0901234501", 120, "Hạng Đồng"),
                ("khach2@gmail.com", "Trần Văn Nam", "0901234502", 780, "Hạng Bạc"),
                ("khach3@gmail.com", "Lê Thị Mai", "0901234503", 2650, "Hạng Vàng"),
                ("khach4@gmail.com", "Phạm Minh Tuấn", "0901234504", 350, "Hạng Đồng"),
                ("khach5@gmail.com", "Hoàng Thu Hà", "0901234505", 5200, "Hạng Bạch Kim"),
            ],
        )

        print("\n  -- Transactions, ledger, vouchers, redemptions --")
        await _seed_transactions_and_ledger(
            db, tenant=ctx1["tenant"], owner=owner1, memberships=ctx1["memberships"], count=30
        )
        await _seed_vouchers(
            db, tenant=ctx1["tenant"], memberships=ctx1["memberships"], campaigns=ctx1["campaigns"]
        )
        await _seed_redemptions(
            db, tenant=ctx1["tenant"], memberships=ctx1["memberships"], rewards=ctx1["rewards"]
        )

        # ===== Tenant 2: Trà Sữa Lala =====
        print("\n[3] Tenant 2 — Trà Sữa Lala")
        owner2 = await _get_or_create_user(
            db,
            email="owner@lala.vn",
            password="owner1234",
            full_name="Nguyễn Thị Lan",
            phone="0912345002",
        )
        ctx2 = await _seed_tenant(
            db,
            name="Trà Sữa Lala",
            slug="tra-sua-lala",
            owner=owner2,
            description="Chuỗi trà sữa hot nhất Sài Gòn",
            tier_names=[
                ("Lala Member", 0),
                ("Lala Silver", 300),
                ("Lala Gold", 1500),
                ("Lala VIP", 4000),
            ],
            rewards=[
                ("Trà sữa topping free", 100, 80),
                ("Set 2 ly trà sữa", 250, 40),
                ("Voucher sinh nhật 100K", 800, None),
            ],
            campaigns=[
                ("Buy 1 Get 1", 50, 30_000),
                ("Giảm 15% Topping", 15, 20_000),
            ],
            customers=[
                ("lala1@gmail.com", "Vũ Minh Anh", "0902234501", 90, "Lala Member"),
                ("lala2@gmail.com", "Đỗ Hương Giang", "0902234502", 480, "Lala Silver"),
                ("lala3@gmail.com", "Bùi Quang Huy", "0902234503", 1820, "Lala Gold"),
                ("lala4@gmail.com", "Ngô Thu Trang", "0902234504", 4500, "Lala VIP"),
                ("lala5@gmail.com", "Lý Hoàng Phúc", "0902234505", 210, "Lala Member"),
            ],
        )

        print("\n  -- Transactions, ledger, vouchers, redemptions --")
        await _seed_transactions_and_ledger(
            db, tenant=ctx2["tenant"], owner=owner2, memberships=ctx2["memberships"], count=35
        )
        await _seed_vouchers(
            db, tenant=ctx2["tenant"], memberships=ctx2["memberships"], campaigns=ctx2["campaigns"]
        )
        await _seed_redemptions(
            db, tenant=ctx2["tenant"], memberships=ctx2["memberships"], rewards=ctx2["rewards"]
        )

        await db.commit()
        print("\n" + "=" * 50)
        print("✅ Seed completed")
        print("=" * 50)
        print("\n🔑 Accounts:")
        print("  Super Admin:      admin@loyalty.vn         / admin1234")
        print("\n  Merchant Owners:")
        print("   - owner@cafe.vn    (Cafe Cộng)            / owner1234")
        print("   - owner@lala.vn    (Trà Sữa Lala)         / owner1234")
        print("\n  Customers Cafe Cộng (tenant 1):")
        print("   - khach1@gmail.com  → Hạng Đồng  (120 điểm)")
        print("   - khach2@gmail.com  → Hạng Bạc   (780 điểm)")
        print("   - khach3@gmail.com  → Hạng Vàng  (2650 điểm)")
        print("   - khach4@gmail.com  → Hạng Đồng  (350 điểm)")
        print("   - khach5@gmail.com  → Hạng Bạch Kim (5200 điểm)")
        print("\n  Customers Trà Sữa Lala (tenant 2):")
        print("   - lala1@gmail.com   → Lala Member (90 điểm)")
        print("   - lala2@gmail.com   → Lala Silver (480 điểm)")
        print("   - lala3@gmail.com   → Lala Gold   (1820 điểm)")
        print("   - lala4@gmail.com   → Lala VIP    (4500 điểm)")
        print("   - lala5@gmail.com   → Lala Member (210 điểm)")
        print("\n  Mật khẩu tất cả customer: khach1234")


if __name__ == "__main__":
    asyncio.run(main())
