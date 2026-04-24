"""NotificationService — push + list + mark_read."""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def push(
        self,
        *,
        user_id: int,
        partner_id: int | None = None,
        type: str,
        title: str,
        body: str | None = None,
        data: dict | None = None,
    ) -> Notification:
        """Tạo notification mới cho user."""
        notif = Notification(
            user_id=user_id,
            partner_id=partner_id,
            type=type,
            title=title,
            body=body,
            data=data or {},
            is_read=False,
        )
        self.db.add(notif)
        await self.db.flush()
        return notif

    async def list_user(
        self,
        *,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        """List notifications cho user, mới nhất trước."""
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        rows = await self.db.scalars(stmt)
        return list(rows.all())

    async def count_unread(self, *, user_id: int) -> int:
        """Đếm notification chưa đọc."""
        from sqlalchemy import func

        result = await self.db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        return int(result or 0)

    async def mark_read(self, *, user_id: int, notification_ids: list[int]) -> int:
        """Mark notifications as read. Return số rows updated."""
        result = await self.db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.id.in_(notification_ids),
                Notification.is_read.is_(False),
            )
            .values(is_read=True)
        )
        await self.db.flush()
        return result.rowcount
