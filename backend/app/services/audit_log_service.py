from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def log(
        self,
        *,
        actor_user_id: int | None,
        action: str,
        target_type: str,
        target_id: int | None = None,
        reason: str | None = None,
        before_snapshot: dict[str, Any] | None = None,
        after_snapshot: dict[str, Any] | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
        )
        self.db.add(entry)
        # Caller is responsible for commit; we only flush to get the id if needed.
        await self.db.flush()
        return entry

    async def list(
        self,
        *,
        actor_user_id: int | None = None,
        target_type: str | None = None,
        target_id: int | None = None,
        action: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        q = select(AuditLog)
        cq = select(func.count()).select_from(AuditLog)

        if actor_user_id is not None:
            q = q.where(AuditLog.actor_user_id == actor_user_id)
            cq = cq.where(AuditLog.actor_user_id == actor_user_id)
        if target_type is not None:
            q = q.where(AuditLog.target_type == target_type)
            cq = cq.where(AuditLog.target_type == target_type)
        if target_id is not None:
            q = q.where(AuditLog.target_id == target_id)
            cq = cq.where(AuditLog.target_id == target_id)
        if action is not None:
            q = q.where(AuditLog.action == action)
            cq = cq.where(AuditLog.action == action)

        total_result = await self.db.execute(cq)
        total = total_result.scalar_one()

        q = q.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(q)
        rows = list(result.scalars().all())
        return rows, total
