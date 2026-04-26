from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.login_log import LoginLog


class LoginLogService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_attempt(
        self,
        *,
        identifier: str,
        ip: str,
        success: bool,
        user_id: int | None = None,
        user_agent: str | None = None,
        failure_reason: str | None = None,
    ) -> LoginLog:
        ua = user_agent[:500] if user_agent else None
        log = LoginLog(
            identifier=identifier,
            ip=ip,
            success=success,
            user_id=user_id,
            user_agent=ua,
            failure_reason=failure_reason,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def count_recent_failures(self, identifier: str, *, minutes: int = 15) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return (await self.db.scalar(
            select(func.count())
            .select_from(LoginLog)
            .where(
                LoginLog.identifier == identifier,
                LoginLog.success.is_(False),
                LoginLog.created_at > cutoff,
            )
        )) or 0
