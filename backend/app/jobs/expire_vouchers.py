"""Job expire_vouchers — Phase 11.

Chạy hourly. Set `status='expired'` cho voucher `status='issued'` đã qua
`expires_at`. Bulk UPDATE 1 câu; idempotent. Acceptance #15.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import update

from app.core.db import AsyncSessionLocal
from app.models.voucher import Voucher, VoucherStatus

logger = logging.getLogger(__name__)


async def expire_vouchers_job() -> dict:
    try:
        return await _expire_logic()
    except Exception:
        logger.exception("expire_vouchers_job failed")
        return {"expired": 0, "error": True}


async def _expire_logic() -> dict:
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            update(Voucher)
            .where(
                Voucher.status == VoucherStatus.ISSUED,
                Voucher.expires_at < now,
            )
            .values(status=VoucherStatus.EXPIRED)
        )
        await db.commit()
        count = result.rowcount or 0
    logger.info("expire_vouchers: expired=%d", count)
    return {"expired": count}
