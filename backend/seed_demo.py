"""Seed data phong phú cho demo + test.

Tạo 2 đối tác độc lập (Cafe Cộng + Trà Sữa Lala) với đầy đủ:
- tier, point_rule, reward
- 5 customer/đối tác + membership với tier đa dạng
- 14 ngày transactions (~30 txn/đối tác)
- point_ledger entries (earn + adjust + redeem)
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
from app.models.membership import Membership
from app.models.point_ledger import LedgerReason, LedgerRefType, PointLedger
from app.models.point_rule import PointRule
from app.models.redemption import Redemption, RedemptionStatus
from app.models.reward import Reward
from app.models.partner import Partner, PartnerCategory, PartnerStatus
from app.models.partner_staff import PartnerStaff, PartnerStaffRole
from app.models.tier import Tier
from app.models.transaction import Transaction, TransactionMethod
from app.models.user import User


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
    category: PartnerCategory,
    tier_defs: list[tuple[str, int, Decimal]],  # (name, min_points, earn_multiplier)
    use_tiers: bool,
    rewards: list[tuple[str, int, int | None]],
    customers: list[tuple[str, str, str, int, str]],  # (email, name, phone, points, tier_name)
    logo_url: str | None = None,
    banner_url: str | None = None,
    contact_phone: str | None = None,
    contact_email: str | None = None,
    address: str | None = None,
    website: str | None = None,
    business_hours: str | None = None,
) -> dict:
    """Seed 1 đối tác đầy đủ. Trả về dict với các id cần thiết."""
    partner = await db.scalar(select(Partner).where(Partner.slug == slug))
    if partner is None:
        partner = Partner(
            name=name,
            slug=slug,
            owner_user_id=owner.id,
            status=PartnerStatus.ACTIVE,
            category=category,
            description=description,
            logo_url=logo_url,
            banner_url=banner_url,
            contact_phone=contact_phone,
            contact_email=contact_email,
            address=address,
            website=website,
            business_hours=business_hours,
            settings={
                "points_on_gross": False,
                "signup_bonus_points": 100,
                "redemption_default_ttl_days": 14,
            },
            activated_at=datetime.now(UTC),
        )
        db.add(partner)
        await db.flush()
        db.add(PartnerStaff(partner_id=partner.id, user_id=owner.id, role=PartnerStaffRole.OWNER))
        await db.flush()
        print(f"✓ Partner: {name} (id={partner.id})")
    else:
        # Backfill category cho partner đã tồn tại trước migration
        if partner.category != category:
            partner.category = category
            await db.flush()
            print(f"  ↻ Cập nhật category cho {name}: {category}")
        # Backfill các field profile chỉ khi đang null (không ghi đè data owner đã sửa)
        profile_updates = {
            "logo_url": logo_url,
            "banner_url": banner_url,
            "contact_phone": contact_phone,
            "contact_email": contact_email,
            "address": address,
            "website": website,
            "business_hours": business_hours,
        }
        backfilled = []
        for field, value in profile_updates.items():
            if value is not None and getattr(partner, field) is None:
                setattr(partner, field, value)
                backfilled.append(field)
        if backfilled:
            await db.flush()
            print(f"  ↻ Backfill profile: {', '.join(backfilled)}")
        else:
            print(f"- Partner đã tồn tại: {name}")

    # Point rule
    rule = await db.scalar(
        select(PointRule).where(PointRule.partner_id == partner.id, PointRule.is_active.is_(True))
    )
    if rule is None:
        db.add(PointRule(
            partner_id=partner.id,
            unit_amount=10_000,
            points_per_unit=Decimal("1"),
            min_amount=0,
            use_tiers=use_tiers,
            is_active=True,
        ))
        await db.flush()
        print(f"  ✓ Point rule: 10.000₫ = 1 điểm, use_tiers={use_tiers}")
    else:
        # Backfill use_tiers nếu khác
        if rule.use_tiers != use_tiers:
            rule.use_tiers = use_tiers
            await db.flush()
            print(f"  ↻ Backfill point_rule.use_tiers={use_tiers}")

    # Tiers
    existing_tiers = (
        await db.scalars(
            select(Tier).where(Tier.partner_id == partner.id, Tier.deleted_at.is_(None))
        )
    ).all()
    if not existing_tiers:
        for tier_name, min_pts, earn_mult in tier_defs:
            db.add(Tier(
                partner_id=partner.id,
                name=tier_name,
                min_points=min_pts,
                earn_multiplier=earn_mult,
                is_active=True,
            ))
        await db.flush()
        print(f"  ✓ {len(tier_defs)} tiers")
    else:
        # Backfill earn_multiplier cho tier đã tồn tại (theo tên)
        multiplier_map = {t_name: earn_mult for t_name, _, earn_mult in tier_defs}
        updated = 0
        for tier in existing_tiers:
            if tier.name in multiplier_map:
                new_mult = multiplier_map[tier.name]
                if tier.earn_multiplier != new_mult:
                    tier.earn_multiplier = new_mult
                    updated += 1
        if updated:
            await db.flush()
            print(f"  ↻ Backfill earn_multiplier cho {updated} tiers")

    tiers_map = {
        t.name: t
        for t in (
            await db.scalars(
                select(Tier).where(Tier.partner_id == partner.id, Tier.deleted_at.is_(None))
            )
        ).all()
    }

    # Rewards
    existing_rewards = (
        await db.scalars(
            select(Reward).where(Reward.partner_id == partner.id, Reward.deleted_at.is_(None))
        )
    ).all()
    if not existing_rewards:
        for r_name, pts, stock in rewards:
            db.add(Reward(
                partner_id=partner.id,
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
            select(Reward).where(Reward.partner_id == partner.id, Reward.deleted_at.is_(None))
        )
    ).all()

    # Staff accounts (ngoài owner) — seed 2 staff/đối tác để test staff-only flows
    staff_seeds_by_tenant = {
        "cafe-cong": [
            ("staff1@cafe.vn", "Nguyễn Thu Hằng", "0901111101"),
            ("staff2@cafe.vn", "Trần Quốc Đạt", "0901111102"),
        ],
        "tra-sua-lala": [
            ("staff1@lala.vn", "Phạm Mai Linh", "0902222201"),
            ("staff2@lala.vn", "Hoàng Văn Nam", "0902222202"),
        ],
    }
    for staff_email, staff_name, staff_phone in staff_seeds_by_tenant.get(slug, []):
        staff_user = await _get_or_create_user(
            db,
            email=staff_email,
            password="staff1234",
            full_name=staff_name,
            phone=staff_phone,
        )
        existing_staff = await db.scalar(
            select(PartnerStaff).where(
                PartnerStaff.partner_id == partner.id,
                PartnerStaff.user_id == staff_user.id,
            )
        )
        if existing_staff is None:
            db.add(
                PartnerStaff(
                    partner_id=partner.id,
                    user_id=staff_user.id,
                    role=PartnerStaffRole.STAFF,
                )
            )
            await db.flush()
            print(f"  ✓ Staff {staff_email} → {name}")

    # Customers + memberships
    memberships: list[Membership] = []
    for email, c_name, phone, points, tier_name in customers:
        user = await _get_or_create_user(
            db, email=email, password="khach1234", full_name=c_name, phone=phone,
        )
        membership = await db.scalar(
            select(Membership).where(
                Membership.partner_id == partner.id, Membership.user_id == user.id
            )
        )
        if membership is None:
            tier = tiers_map.get(tier_name)
            membership = Membership(
                partner_id=partner.id,
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
        "partner": partner,
        "owner": owner,
        "tiers": tiers_map,
        "rewards": rewards_list,
        "memberships": memberships,
    }


async def _seed_transactions_and_ledger(
    db, *, partner: Partner, owner: User, memberships: list[Membership], count: int = 30
) -> None:
    """Rải transactions đều trong 14 ngày gần nhất + ghi ledger entries."""
    existing = await db.scalar(
        select(Transaction.id).where(Transaction.partner_id == partner.id).limit(1)
    )
    if existing is not None:
        return

    rng = random.Random(42 + partner.id)  # Deterministic
    now = datetime.now(UTC)
    for i in range(count):
        membership = rng.choice(memberships)
        days_ago = rng.randint(0, 13)
        hours_ago = rng.randint(0, 23)
        created_at = now - timedelta(days=days_ago, hours=hours_ago)
        gross = rng.choice([45_000, 65_000, 85_000, 120_000, 150_000, 180_000, 250_000])
        points_earned = gross // 10_000
        receipt_code = (
            f"HD-{partner.slug.upper()[:6]}-{i + 1:04d}"
            if rng.random() < 0.7
            else None
        )

        txn = Transaction(
            partner_id=partner.id,
            membership_id=membership.id,
            staff_id=owner.id,
            gross_amount=gross,
            net_amount=gross,
            points_earned=points_earned,
            method=TransactionMethod.QR_CUSTOMER,
            note=f"Giao dịch #{i + 1}",
            receipt_code=receipt_code,
        )
        txn.created_at = created_at
        db.add(txn)
        await db.flush()

        # Ledger entry earn
        new_balance = membership.points_balance + points_earned
        db.add(PointLedger(
            partner_id=partner.id,
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
    db, *, partner: Partner, memberships: list[Membership], rewards: list[Reward]
) -> None:
    """Mỗi customer đổi 1 reward từ kho."""
    if not rewards:
        return
    existing = await db.scalar(
        select(Redemption.id).where(Redemption.partner_id == partner.id).limit(1)
    )
    if existing is not None:
        return

    now = datetime.now(UTC)
    for i, membership in enumerate(memberships[:3]):
        reward = rewards[i % len(rewards)]
        if membership.points_balance < reward.points_cost:
            continue
        redemption = Redemption(
            partner_id=partner.id,
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
            partner_id=partner.id,
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

        # ===== Partner 1: Cafe Cộng =====
        print("\n[2] Partner 1 — Cafe Cộng - Bà Triệu")
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
            category=PartnerCategory.CAFE,
            tier_defs=[
                ("Hạng Đồng", 0, Decimal("1.00")),
                ("Hạng Bạc", 500, Decimal("1.25")),
                ("Hạng Vàng", 2000, Decimal("1.50")),
                ("Hạng Bạch Kim", 5000, Decimal("2.00")),
            ],
            use_tiers=True,
            rewards=[
                ("Cafe Latte size M Free", 150, 50),
                ("Bánh ngọt cao cấp", 200, 30),
                ("Phiếu giảm 50K", 500, None),
            ],
            customers=[
                ("khach1@gmail.com", "Nguyễn Thị Hoa", "0901234501", 120, "Hạng Đồng"),
                ("khach2@gmail.com", "Trần Văn Nam", "0901234502", 780, "Hạng Bạc"),
                ("khach3@gmail.com", "Lê Thị Mai", "0901234503", 2650, "Hạng Vàng"),
                ("khach4@gmail.com", "Phạm Minh Tuấn", "0901234504", 350, "Hạng Đồng"),
                ("khach5@gmail.com", "Hoàng Thu Hà", "0901234505", 5200, "Hạng Bạch Kim"),
            ],
        )

        print("\n  -- Transactions, ledger, redemptions --")
        await _seed_transactions_and_ledger(
            db, partner=ctx1["partner"], owner=owner1, memberships=ctx1["memberships"], count=30
        )
        await _seed_redemptions(
            db, partner=ctx1["partner"], memberships=ctx1["memberships"], rewards=ctx1["rewards"]
        )

        # ===== Partner 2: Trà Sữa Lala =====
        print("\n[3] Partner 2 — Trà Sữa Lala")
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
            category=PartnerCategory.FOOD,
            tier_defs=[
                ("Lala Member", 0, Decimal("1.00")),
                ("Lala Silver", 300, Decimal("1.25")),
                ("Lala Gold", 1500, Decimal("1.50")),
                ("Lala VIP", 4000, Decimal("2.00")),
            ],
            use_tiers=False,
            rewards=[
                ("Trà sữa topping free", 100, 80),
                ("Set 2 ly trà sữa", 250, 40),
                ("Quà sinh nhật 100K", 800, None),
            ],
            customers=[
                ("lala1@gmail.com", "Vũ Minh Anh", "0902234501", 90, "Lala Member"),
                ("lala2@gmail.com", "Đỗ Hương Giang", "0902234502", 480, "Lala Silver"),
                ("lala3@gmail.com", "Bùi Quang Huy", "0902234503", 1820, "Lala Gold"),
                ("lala4@gmail.com", "Ngô Thu Trang", "0902234504", 4500, "Lala VIP"),
                ("lala5@gmail.com", "Lý Hoàng Phúc", "0902234505", 210, "Lala Member"),
            ],
        )

        print("\n  -- Transactions, ledger, redemptions --")
        await _seed_transactions_and_ledger(
            db, partner=ctx2["partner"], owner=owner2, memberships=ctx2["memberships"], count=35
        )
        await _seed_redemptions(
            db, partner=ctx2["partner"], memberships=ctx2["memberships"], rewards=ctx2["rewards"]
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
        print("\n  Staff (đối tác):")
        print("   - staff1@cafe.vn, staff2@cafe.vn          / staff1234")
        print("   - staff1@lala.vn, staff2@lala.vn          / staff1234")
        print("\n  Customers Cafe Cộng (đối tác 1):")
        print("   - khach1@gmail.com  → Hạng Đồng  (120 điểm)")
        print("   - khach2@gmail.com  → Hạng Bạc   (780 điểm)")
        print("   - khach3@gmail.com  → Hạng Vàng  (2650 điểm)")
        print("   - khach4@gmail.com  → Hạng Đồng  (350 điểm)")
        print("   - khach5@gmail.com  → Hạng Bạch Kim (5200 điểm)")
        print("\n  Customers Trà Sữa Lala (đối tác 2):")
        print("   - lala1@gmail.com   → Lala Member (90 điểm)")
        print("   - lala2@gmail.com   → Lala Silver (480 điểm)")
        print("   - lala3@gmail.com   → Lala Gold   (1820 điểm)")
        print("   - lala4@gmail.com   → Lala VIP    (4500 điểm)")
        print("   - lala5@gmail.com   → Lala Member (210 điểm)")
        print("\n  Mật khẩu tất cả customer: khach1234")


if __name__ == "__main__":
    asyncio.run(main())
