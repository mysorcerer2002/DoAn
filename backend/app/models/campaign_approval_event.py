"""CampaignApprovalEvent — audit log lifecycle duyệt campaign.

M6 của plan voucher rebuild v2.2. Append-only log: mỗi lần campaign chuyển
trạng thái duyệt (submitted/auto_approved/ops_started/approved/rejected/
revision_requested/cancelled_by_shop) → ghi 1 event.

Không UPDATE/DELETE event đã tạo — giữ nguyên vết cho nghiệp vụ audit Sở CT
và đối chiếu (Luật Kế toán 2015 Điều 41 — lưu 10 năm).
"""

import enum
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ApprovalEventType(str, enum.Enum):
    SUBMITTED = "submitted"
    AUTO_APPROVED = "auto_approved"
    OPS_STARTED = "ops_started"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"
    CANCELLED_BY_SHOP = "cancelled_by_shop"


class CampaignApprovalEvent(Base, TimestampMixin):
    __tablename__ = "campaign_approval_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('submitted','auto_approved','ops_started','approved',"
            "'rejected','revision_requested','cancelled_by_shop')",
            name="ck_campaign_approval_events_event_type",
        ),
        Index(
            "ix_campaign_approval_events_campaign_at",
            "campaign_id",
            "at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="RESTRICT"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
