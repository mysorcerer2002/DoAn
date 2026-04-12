"""API endpoints — /notifications (GET + mark-read)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.notification import MarkReadRequest, NotificationResponse
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationResponse]:
    """List notifications cho current user."""
    notifications = await NotificationService(db).list_user(
        user_id=current_user.id, unread_only=unread_only
    )
    return [NotificationResponse.model_validate(n) for n in notifications]


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    """Đếm notification chưa đọc."""
    count = await NotificationService(db).count_unread(user_id=current_user.id)
    return {"unread_count": count}


@router.post("/mark-read")
async def mark_notifications_read(
    body: MarkReadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    """Mark notifications as read."""
    updated = await NotificationService(db).mark_read(
        user_id=current_user.id, notification_ids=body.notification_ids
    )
    return {"updated": updated}
