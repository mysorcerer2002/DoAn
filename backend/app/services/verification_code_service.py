import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.verification_code import VerificationCode, VerificationCodePurpose


class InvalidCodeError(Exception):
    pass


def _hmac_hash(code: str, secret: str) -> str:
    return hmac.new(secret.encode(), code.encode(), hashlib.sha256).hexdigest()


def _generate_6_digit() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


class VerificationCodeService:
    TTL_MINUTES = 10

    def __init__(self, db: AsyncSession):
        self.db = db
        self._secret = get_settings().jwt_secret

    async def create_code(
        self,
        *,
        user_id: int,
        purpose: VerificationCodePurpose,
        context_hash: str | None = None,
    ) -> str:
        """Sinh code mới + invalidate code cũ chưa dùng. Trả plain code.

        `context_hash` (optional): sha256 của payload cần bind OTP vào —
        verify sẽ fail nếu context mismatch. Dùng ở flow
        `authorization_sign` để chặn tamper form giữa request-otp và sign.
        """
        # Vô hiệu code cũ
        await self.db.execute(
            update(VerificationCode)
            .where(
                VerificationCode.user_id == user_id,
                VerificationCode.purpose == purpose,
                VerificationCode.used_at.is_(None),
            )
            .values(used_at=datetime.now(timezone.utc))
        )

        plain = _generate_6_digit()
        code_hash = _hmac_hash(plain, self._secret)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.TTL_MINUTES)

        record = VerificationCode(
            user_id=user_id,
            code_hash=code_hash,
            purpose=purpose,
            expires_at=expires_at,
            context_hash=context_hash,
        )
        self.db.add(record)
        await self.db.flush()

        return plain

    async def verify_code(
        self,
        *,
        user_id: int,
        code: str,
        purpose: VerificationCodePurpose,
        context_hash: str | None = None,
    ) -> bool:
        """Verify OTP; fail nếu sai / hết hạn / đã dùng / context mismatch.

        Dùng `SELECT ... FOR UPDATE` để serialize concurrent sign với cùng
        OTP — request thứ 2 block đến khi request 1 commit rồi mới thấy
        `used_at IS NOT NULL` và fail.
        """
        code_hash = _hmac_hash(code, self._secret)
        now = datetime.now(timezone.utc)

        record = await self.db.scalar(
            select(VerificationCode)
            .where(
                VerificationCode.user_id == user_id,
                VerificationCode.code_hash == code_hash,
                VerificationCode.purpose == purpose,
                VerificationCode.used_at.is_(None),
                VerificationCode.expires_at > now,
            )
            .with_for_update()
        )
        if record is None:
            raise InvalidCodeError("Invalid, expired, or already used code")

        # Fail-closed: nếu OTP lúc phát được bind vào context_hash (sign uỷ
        # quyền), mọi request verify sau đó PHẢI gửi context_hash khớp —
        # bỏ qua `is not None` tránh bypass bằng cách gọi verify không kèm
        # context_hash.
        if record.context_hash != context_hash:
            raise InvalidCodeError("OTP context mismatch")

        record.used_at = now
        await self.db.flush()
        return True
