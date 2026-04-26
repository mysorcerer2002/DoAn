"""QR Service — decode raw user_id QR payload + DB lookup."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.membership import Membership
from app.models.user import User


class QrPayloadInvalidError(Exception):
    pass


class QrUserNotFoundError(Exception):
    pass


class QrUserNotMemberError(Exception):
    pass


class QrService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def decode_qr_payload(
        self, payload: str, partner_id: int
    ) -> tuple[User, Membership]:
        """Decode raw user_id QR payload → (User, Membership).

        Args:
            payload: Raw string số (user_id) từ QR cá nhân khách.
            partner_id: Partner context để lookup membership.

        Returns:
            (user, membership) với membership đã lock FOR UPDATE.

        Raises:
            QrPayloadInvalidError nếu payload không phải số nguyên dương.
            QrUserNotFoundError nếu user không tồn tại hoặc bị khoá.
            QrUserNotMemberError nếu user chưa là thành viên của partner này.
        """
        try:
            user_id = int(payload.strip())
            if user_id <= 0:
                raise ValueError
        except (ValueError, AttributeError):
            raise QrPayloadInvalidError("QR payload không hợp lệ.")

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
            raise QrUserNotMemberError("Khách hàng chưa là thành viên shop này.")

        return user, membership
