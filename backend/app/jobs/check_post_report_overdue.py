"""Job check_post_report_overdue — Phase 11.

Chạy daily 01:00. Find campaign `approval_status IN ('auto_approved',
'approved')` có `post_report_due_at < NOW()` AND
`post_report_submitted_at IS NULL`, log WARNING cho ops quét.

v1: log only (acceptance #14 chỉ yêu cầu notify; v2 sẽ push admin
notification row vào `notifications` table).
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.models.campaign import Campaign

logger = logging.getLogger(__name__)


async def check_post_report_overdue_job() -> dict:
    try:
        return await _overdue_logic()
    except Exception:
        logger.exception("check_post_report_overdue_job failed")
        return {"overdue_count": 0, "error": True}


async def _overdue_logic() -> dict:
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        rows = (
            await db.scalars(
                select(Campaign).where(
                    Campaign.approval_status.in_(("auto_approved", "approved")),
                    Campaign.post_report_due_at.is_not(None),
                    Campaign.post_report_due_at < now,
                    Campaign.post_report_submitted_at.is_(None),
                    Campaign.deleted_at.is_(None),
                )
            )
        ).all()
    for c in rows:
        overdue_days = (now - c.post_report_due_at).days
        logger.warning(
            "Campaign #%d (partner=%d) quá hạn báo cáo kết thúc %d ngày "
            "(due=%s, name=%s)",
            c.id,
            c.partner_id,
            overdue_days,
            c.post_report_due_at,
            c.name,
        )
    logger.info("check_post_report_overdue: %d overdue campaigns", len(rows))
    return {"overdue_count": len(rows)}
