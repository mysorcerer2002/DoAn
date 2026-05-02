"""QR Service — decode raw user_id QR payload + DB lookup + auto-enroll."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.membership import Membership
from app.models.user import User


class QrPayloadInvalidError(Exception):
    pass


class QrUserNotFoundError(Exception):
    pass


class QrService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def decode_qr_payload(
        self, payload: str, partner_id: int
    ) -> tuple[User, Membership]:
        """Decode QR payload (raw user_id) → (User, Membership).

        Auto-enroll: nếu user chưa là member shop → tạo membership mới
        (lifetime_earned=0, current_tier_id=NULL). UniqueConstraint
        (partner_id, user_id) đảm bảo concurrent scan an toàn.
        """
        try:
            user_id = int(payload.strip())
            if user_id <= 0:
                raise ValueError
        except (ValueError, AttributeError) as e:
            raise QrPayloadInvalidError("QR payload không hợp lệ.") from e

        user = await self.db.get(User, user_id)
        if user is None or not user.is_active:
            raise QrUserNotFoundError("Không tìm thấy khách hàng từ QR.")

        membership = await self.db.scalar(
            select(Membership)
            .options(
                joinedload(Membership.user, innerjoin=True),
                selectinload(Membership.current_tier),
            )
            .where(
                Membership.partner_id == partner_id,
                Membership.user_id == user_id,
            )
            .with_for_update()
        )
        if membership is None:
            # Auto-enroll
            try:
                async with self.db.begin_nested():
                    new_m = Membership(
                        partner_id=partner_id,
                        user_id=user_id,
                        current_tier_id=None,
                        joined_at=datetime.now(timezone.utc),
                    )
                    self.db.add(new_m)
                    await self.db.flush()
            except IntegrityError:
                pass  # Concurrent scan đã tạo, re-fetch

            membership = await self.db.scalar(
                select(Membership)
                .options(
                    joinedload(Membership.user, innerjoin=True),
                    selectinload(Membership.current_tier),
                )
                .where(
                    Membership.partner_id == partner_id,
                    Membership.user_id == user_id,
                )
                .with_for_update()
            )
            if membership is None:
                raise QrUserNotFoundError(
                    f"Không thể tạo membership cho user {user_id} tại partner {partner_id}"
                )

        return user, membership
