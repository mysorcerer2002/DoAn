"""VoucherTemplate model — Hybrid C+i (Admin upload PNG khung + JSONB layout)."""

import enum

from sqlalchemy import JSON, Boolean, CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class VoucherTemplateCategory(str, enum.Enum):
    CAFE = "CAFE"
    FOOD = "FOOD"
    RETAIL = "RETAIL"
    BEAUTY = "BEAUTY"
    SEASONAL = "SEASONAL"
    OTHER = "OTHER"


class VoucherTemplate(Base, TimestampMixin):
    """Khung voucher dùng chung cho mọi shop. Reward.template_id reference (nullable)."""

    __tablename__ = "voucher_templates"
    __table_args__ = (
        # Suffix-only — convention prepend `ck_voucher_templates_`.
        CheckConstraint(
            "category IN ('CAFE','FOOD','RETAIL','BEAUTY','SEASONAL','OTHER')",
            name="valid_category",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[VoucherTemplateCategory] = mapped_column(String(20), nullable=False)
    frame_image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    text_layout_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
