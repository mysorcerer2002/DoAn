"""QR Service — wrapper cho QR JWT core logic + DB lookup."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.qr import (
    InvalidQRError,
    decode_qr_jwt,
    sign_qr_jwt,
    verify_fallback_code_with_candidates,
)
from app.models.membership import Membership


class QrService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def issue_qr_for_user(self, user_id: int) -> dict:
        """Issue QR token + fallback_code cho user."""
        return sign_qr_jwt(user_id=user_id)

    async def decode_qr_payload(
        self, *, payload: str, tenant_id: int
    ) -> int:
        """Decode QR payload → user_id.

        Args:
            payload: Có thể là JWT (chuỗi dài) hoặc fallback_code (8 ký tự)
            tenant_id: Tenant context để lookup candidate user_ids cho fallback

        Returns:
            user_id

        Raises:
            InvalidQRError nếu payload không hợp lệ
        """
        # Heuristic: JWT có 3 phần ngăn cách bởi '.'; fallback_code 8 ký tự alnum
        if "." in payload and len(payload) > 20:
            return decode_qr_jwt(payload)

        # Fallback code path — lookup tất cả member của tenant hiện tại
        candidates = list(
            (
                await self.db.scalars(
                    select(Membership.user_id).where(
                        Membership.tenant_id == tenant_id
                    )
                )
            ).all()
        )
        if not candidates:
            raise InvalidQRError("No members in tenant")
        return verify_fallback_code_with_candidates(
            payload, candidate_user_ids=candidates
        )
