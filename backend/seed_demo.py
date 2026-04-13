"""Seed data tối thiểu cho demo: tạo super admin + 1 tenant active + 1 rule + 1 reward."""

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.core.security import hash_password
from app.models.campaign import Campaign, DiscountType
from app.models.point_rule import PointRule
from app.models.reward import Reward
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_staff import TenantStaff, TenantStaffRole
from app.models.tier import Tier
from app.models.user import User


async def main() -> None:
    async with AsyncSessionLocal() as db:
        # 1. Super admin
        admin = await db.scalar(select(User).where(User.email == "admin@loyalty.vn"))
        if admin is None:
            admin = User(
                email="admin@loyalty.vn",
                password_hash=hash_password("admin1234"),
                full_name="Super Admin",
                is_active=True,
                system_role="super_admin",
                password_changed_at=datetime.now(UTC),
            )
            db.add(admin)
            await db.flush()
            print(f"✓ Tạo super admin: admin@loyalty.vn / admin1234")
        else:
            print(f"- Super admin đã tồn tại: {admin.email}")

        # 2. Owner user
        owner = await db.scalar(select(User).where(User.email == "owner@cafe.vn"))
        if owner is None:
            owner = User(
                email="owner@cafe.vn",
                password_hash=hash_password("owner1234"),
                full_name="Lê Văn Bình",
                is_active=True,
                system_role="regular",
                password_changed_at=datetime.now(UTC),
            )
            db.add(owner)
            await db.flush()
            print(f"✓ Tạo owner: owner@cafe.vn / owner1234")
        else:
            print(f"- Owner đã tồn tại: {owner.email}")

        # 3. Active tenant
        tenant = await db.scalar(select(Tenant).where(Tenant.slug == "cafe-cong"))
        if tenant is None:
            tenant = Tenant(
                name="Cafe Cộng - Bà Triệu",
                slug="cafe-cong",
                owner_user_id=owner.id,
                status=TenantStatus.ACTIVE,
                description="Quán cafe phong cách Việt Nam",
                logo_url=None,
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
            db.add(
                TenantStaff(
                    tenant_id=tenant.id,
                    user_id=owner.id,
                    role=TenantStaffRole.OWNER,
                )
            )
            await db.flush()
            print(f"✓ Tạo tenant: {tenant.name} (id={tenant.id})")
        else:
            print(f"- Tenant đã tồn tại: {tenant.name}")

        # 4. Point rule
        rule = await db.scalar(
            select(PointRule).where(
                PointRule.tenant_id == tenant.id, PointRule.is_active.is_(True)
            )
        )
        if rule is None:
            rule = PointRule(
                tenant_id=tenant.id,
                unit_amount=10_000,
                points_per_unit=Decimal("1"),
                min_amount=0,
                is_active=True,
            )
            db.add(rule)
            await db.flush()
            print("✓ Tạo point rule: 10.000₫ = 1 điểm")

        # 5. Tiers
        existing_tiers = (
            await db.scalars(
                select(Tier).where(
                    Tier.tenant_id == tenant.id, Tier.deleted_at.is_(None)
                )
            )
        ).all()
        if not existing_tiers:
            for name, min_pts in [
                ("Hạng Đồng", 0),
                ("Hạng Bạc", 500),
                ("Hạng Vàng", 2000),
                ("Hạng Bạch Kim", 5000),
            ]:
                db.add(
                    Tier(
                        tenant_id=tenant.id,
                        name=name,
                        min_points=min_pts,
                        is_active=True,
                    )
                )
            await db.flush()
            print("✓ Tạo 4 tiers (Đồng → Bạch Kim)")

        # 6. Sample rewards
        existing_rewards = (
            await db.scalars(
                select(Reward).where(
                    Reward.tenant_id == tenant.id, Reward.deleted_at.is_(None)
                )
            )
        ).all()
        if not existing_rewards:
            for name, pts, stock in [
                ("Cafe Latte size M Free", 150, 50),
                ("Bánh ngọt cao cấp", 200, 30),
                ("Voucher giảm 50K", 500, None),
            ]:
                db.add(
                    Reward(
                        tenant_id=tenant.id,
                        name=name,
                        description=f"Đổi điểm lấy {name.lower()}",
                        points_cost=pts,
                        stock=stock,
                        is_active=True,
                    )
                )
            await db.flush()
            print("✓ Tạo 3 rewards mẫu")

        # 7. Sample campaign
        campaign = await db.scalar(
            select(Campaign).where(
                Campaign.tenant_id == tenant.id, Campaign.name == "Giảm 20% Coffee"
            )
        )
        if campaign is None:
            now = datetime.now(UTC)
            db.add(
                Campaign(
                    tenant_id=tenant.id,
                    name="Giảm 20% Coffee",
                    description="Áp dụng cho mọi món Coffee",
                    source="manual",
                    discount_type=DiscountType.PERCENT,
                    discount_value=20,
                    max_discount=50_000,
                    min_order=50_000,
                    starts_at=now - timedelta(days=1),
                    ends_at=now + timedelta(days=30),
                    max_issuances=1000,
                    is_active=True,
                )
            )
            await db.flush()
            print("✓ Tạo campaign: Giảm 20% Coffee")

        await db.commit()
        print("\n✅ Seed completed!")
        print("\n🔑 Accounts:")
        print("  Admin: admin@loyalty.vn / admin1234")
        print("  Owner: owner@cafe.vn / owner1234")
        print(f"  Tenant: {tenant.name} (id={tenant.id}, slug={tenant.slug})")


if __name__ == "__main__":
    asyncio.run(main())
