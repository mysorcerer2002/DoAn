"""Job purge_retention — Phase 11.

Chạy weekly (Sunday 02:00 giờ VN). Hard-delete
`partner_authorizations` và `campaign_service_fees` có
`retention_until < NOW()` (Luật Kế toán 2015 Điều 41 — giữ chứng từ kế
toán ≥ 10 năm). Acceptance #18.

**FK safety:**
- `campaigns.authorization_id` ON DELETE SET NULL → xoá authorization
  an toàn, campaign không vỡ FK.
- `campaign_service_fees.campaign_id` ON DELETE RESTRICT — nhưng job
  này chỉ xoá fee (không đụng campaign) nên không vướng.

**Concurrency (I1):** dùng `pg_advisory_xact_lock` serialize giữa 2
instance scheduler song song (dev + prod, hoặc replica scale-out). Lock
auto release khi commit/rollback. `DELETE ... RETURNING id` một câu —
SELECT ids + DELETE không thể drift giữa nhau.

v1: audit qua `logger.warning` (docker logs/stdout). Nếu cần audit
durable sau này, thêm bảng `retention_purge_events(id, run_at,
table_name, deleted_ids, count)` ở phase riêng — plan đã flag.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import text

from app.core.db import AsyncSessionLocal

logger = logging.getLogger(__name__)

# Advisory lock key — hashtext('retention_purge'). Phải ổn định giữa các
# instance. Dùng BIGINT để tránh collision với advisory lock khác.
_PURGE_LOCK_KEY = 0x7265_7465_6e74_696f  # ascii 'retentio' — 8 bytes


async def purge_retention_job() -> dict:
    try:
        return await _purge_logic()
    except Exception:
        logger.exception("purge_retention_job failed")
        return {"auth_deleted": 0, "fee_deleted": 0, "error": True}


async def _purge_logic() -> dict:
    async with AsyncSessionLocal() as db:
        # Transaction-scoped advisory lock: nếu instance khác đang chạy,
        # chờ nó xong rồi mới tiếp (tránh double-audit-log).
        await db.execute(
            text("SELECT pg_advisory_xact_lock(:key)"),
            {"key": _PURGE_LOCK_KEY},
        )

        # DELETE ... RETURNING id — atomic, không TOCTOU.
        auth_result = await db.execute(
            text(
                "DELETE FROM partner_authorizations "
                "WHERE retention_until < :now RETURNING id"
            ),
            {"now": datetime.now(timezone.utc)},
        )
        auth_ids = [row[0] for row in auth_result.fetchall()]

        fee_result = await db.execute(
            text(
                "DELETE FROM campaign_service_fees "
                "WHERE retention_until < :now RETURNING id"
            ),
            {"now": datetime.now(timezone.utc)},
        )
        fee_ids = [row[0] for row in fee_result.fetchall()]

        await db.commit()

    if auth_ids:
        logger.warning(
            "purge_retention: hard-delete %d partner_authorizations ids=%s",
            len(auth_ids),
            auth_ids,
        )
    if fee_ids:
        logger.warning(
            "purge_retention: hard-delete %d campaign_service_fees ids=%s",
            len(fee_ids),
            fee_ids,
        )
    logger.info(
        "purge_retention: auth_deleted=%d fee_deleted=%d",
        len(auth_ids),
        len(fee_ids),
    )
    return {"auth_deleted": len(auth_ids), "fee_deleted": len(fee_ids)}
