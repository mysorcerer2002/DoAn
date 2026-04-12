"""Schemas cho Notification."""

from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    tenant_id: int | None
    user_id: int
    type: str
    title: str
    body: str | None
    data: dict
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MarkReadRequest(BaseModel):
    notification_ids: list[int]
