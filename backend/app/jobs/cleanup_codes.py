"""Job: xoá verification_codes hết hạn > 1 ngày."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from app.core.db import AsyncSessionLocal
from app.models.verification_code import VerificationCode

logger = logging.getLogger(__name__)


async def cleanup_expired_verification_codes() -> int:
    """Xoá verification codes đã hết hạn quá 1 ngày."""
    try:
        return await _cleanup_logic()
    except Exception:
        logger.exception("cleanup_expired_verification_codes failed")
        return 0


async def _cleanup_logic() -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=1)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            delete(VerificationCode).where(VerificationCode.expires_at < cutoff)
        )
        await db.commit()
        deleted_count = result.rowcount
        logger.info(
            "cleanup_expired_verification_codes: deleted %d rows", deleted_count
        )
        return deleted_count
