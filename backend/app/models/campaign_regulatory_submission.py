"""CampaignRegulatorySubmission — hồ sơ nộp Sở Công Thương cho campaign.

M5 của plan voucher rebuild v2.2. Ops staff upload bằng chứng đã nộp
`notify_so_ct` (NĐ 81/2018 Điều 17) hoặc `dang_ky_so_ct` (Điều 19), cũng
như các loại hồ sơ kèm theo (điều lệ, dự toán, xác nhận, báo cáo kết thúc).

`xac_nhan_so_ct` tồn tại là điều kiện để admin `approve` campaign
(xem plan section 4.4 approve guard).
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


class RegulatoryDocType(str, enum.Enum):
    """Các loại tài liệu hồ sơ khuyến mãi (NĐ 81/2018)."""

    NOTIFY_SO_CT = "notify_so_ct"
    DANG_KY_SO_CT = "dang_ky_so_ct"
    DIEU_LE = "dieu_le"
    DU_TOAN = "du_toan"
    XAC_NHAN_SO_CT = "xac_nhan_so_ct"
    BAO_CAO_KET_THUC = "bao_cao_ket_thuc"


class CampaignRegulatorySubmission(Base, TimestampMixin):
    __tablename__ = "campaign_regulatory_submissions"
    __table_args__ = (
        CheckConstraint(
            "doc_type IN ('notify_so_ct','dang_ky_so_ct','dieu_le','du_toan',"
            "'xac_nhan_so_ct','bao_cao_ket_thuc')",
            name="ck_campaign_regulatory_submissions_doc_type",
        ),
        Index(
            "ix_campaign_regulatory_submissions_campaign",
            "campaign_id",
            "doc_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="RESTRICT"), nullable=False
    )
    doc_type: Mapped[str] = mapped_column(String(30), nullable=False)
    reference_no: Mapped[str | None] = mapped_column(String(120), nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    submitted_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
