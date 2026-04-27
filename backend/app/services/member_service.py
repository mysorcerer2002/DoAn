from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.phone import normalize_phone
from app.models.membership import Membership
from app.models.user import User
from app.schemas.member import MemberResponse


class MemberService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_or_create_member(
        self, *, partner_id: int, phone: str
    ) -> MemberResponse:
        """Atomic upsert user theo phone + upsert membership.

        Dùng SAVEPOINT (begin_nested) để bảo vệ outer transaction khi
        IntegrityError xảy ra trong race window — chỉ rollback phần insert
        thay vì cả transaction cha.

        Handles 2 cases:
        - Case 1: User chưa tồn tại → tạo user mới + membership
        - Case 2: User đã tồn tại → chỉ tạo membership
        """
        normalized = normalize_phone(phone)

        existing_user = await self.db.scalar(
            select(User).where(User.phone == normalized)
        )

        if existing_user is None:
            try:
                async with self.db.begin_nested():
                    existing_user = User(
                        phone=normalized,
                        is_active=True,
                        system_role="regular",
                    )
                    self.db.add(existing_user)
                    await self.db.flush()
            except IntegrityError:
                # Race: another connection inserted user with same phone first
                existing_user = await self.db.scalar(
                    select(User).where(User.phone == normalized)
                )
                if existing_user is None:
                    raise

        existing_membership = await self.db.scalar(
            select(Membership)
            .options(joinedload(Membership.current_tier))
            .where(
                Membership.partner_id == partner_id,
                Membership.user_id == existing_user.id,
            )
        )

        is_membership_new = False
        if existing_membership is None:
            try:
                async with self.db.begin_nested():
                    existing_membership = Membership(
                        partner_id=partner_id,
                        user_id=existing_user.id,
                        current_tier_id=None,
                        joined_at=datetime.now(timezone.utc),
                    )
                    self.db.add(existing_membership)
                    await self.db.flush()
                await self.db.refresh(
                    existing_membership, attribute_names=["current_tier"]
                )
                is_membership_new = True
            except IntegrityError:
                # Race: another connection created membership with same (partner, user) first
                existing_membership = await self.db.scalar(
                    select(Membership)
                    .options(joinedload(Membership.current_tier))
                    .where(
                        Membership.partner_id == partner_id,
                        Membership.user_id == existing_user.id,
                    )
                )
                if existing_membership is None:
                    raise

        return MemberResponse(
            membership_id=existing_membership.id,
            partner_id=partner_id,
            user_id=existing_user.id,
            user_phone=existing_user.phone,
            user_full_name=existing_user.full_name,
            user_email=existing_user.email,
            points_balance=existing_user.points_balance,
            lifetime_earned=existing_membership.lifetime_earned,
            current_tier_id=existing_membership.current_tier_id,
            current_tier_name=existing_membership.current_tier.name
            if existing_membership.current_tier
            else None,
            joined_at=existing_membership.joined_at,
            last_activity_at=existing_membership.last_activity_at,
            is_active=existing_membership.is_active,
            is_new=is_membership_new,
        )

    async def get_member_by_id(
        self, *, partner_id: int, membership_id: int
    ) -> Membership | None:
        return await self.db.scalar(
            select(Membership)
            .options(joinedload(Membership.user), joinedload(Membership.current_tier))
            .where(
                Membership.id == membership_id,
                Membership.partner_id == partner_id,
            )
        )

    async def list_members(
        self,
        *,
        partner_id: int,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Membership]:
        stmt = (
            select(Membership)
            .options(joinedload(Membership.user), joinedload(Membership.current_tier))
            .where(Membership.partner_id == partner_id)
        )
        if search:
            search_lc = f"%{search.lower()}%"
            stmt = stmt.join(Membership.user).where(
                (User.phone.ilike(search_lc))
                | (User.email.ilike(search_lc))
                | (User.full_name.ilike(search_lc))
            )
        stmt = (
            stmt.order_by(
                Membership.last_activity_at.desc().nullslast(),
                Membership.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        rows = await self.db.scalars(stmt)
        return list(rows.unique().all())
