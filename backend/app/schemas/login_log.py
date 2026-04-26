from datetime import datetime

from pydantic import BaseModel


class LoginLogResponse(BaseModel):
    id: int
    user_id: int | None
    identifier: str
    ip: str
    user_agent: str | None
    success: bool
    failure_reason: str | None
    created_at: datetime
    user_email: str | None = None  # populated by service via JOIN

    model_config = {"from_attributes": True}


class LoginLogListResponse(BaseModel):
    items: list[LoginLogResponse]
    total: int
    limit: int
    offset: int
