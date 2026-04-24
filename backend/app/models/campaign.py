"""Campaign model — chiến dịch khuyến mãi voucher.

Sau M2a/M2b/M2c (plan voucher rebuild v2.2):
- Liên kết `campaign_templates` qua `template_id` + `template_version_snapshot`.
- State machine approval: draft → pending_approval → auto_approved | approved
  | rejected | revision_requested.
- Approval tier: none | notify_so_ct | dang_ky_so_ct | full_dossier (NĐ 81).
- Cost tracking: `estimated_cost` (tại enroll) + `realized_cost` (update khi
  voucher redeem).
- Audit: `created_by_user_id`, `reviewed_by_user_id`, `reviewed_at`,
  `rejection_reason`, `ops_filing_started_at`, `post_report_*_at`.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class DiscountType(str, enum.Enum):
    PERCENT = "percent"
    FIXED = "fixed"


class CampaignSource(str, enum.Enum):
    MANUAL = "manual"
    BIRTHDAY = "birthday"
    SIGNUP = "signup"


class ApprovalStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    AUTO_APPROVED = "auto_approved"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"


class ApprovalTier(str, enum.Enum):
    NONE = "none"
    NOTIFY_SO_CT = "notify_so_ct"
    DANG_KY_SO_CT = "dang_ky_so_ct"
    FULL_DOSSIER = "full_dossier"


class ServiceFeeStatus(str, enum.Enum):
    NONE = "none"
    ESTIMATED = "estimated"
    INVOICED = "invoiced"
    PAID = "paid"


class Campaign(Base, TimestampMixin):
    """Chiến dịch khuyến mãi — max_issuances NULL = unlimited, soft delete qua deleted_at."""

    __tablename__ = "campaigns"
    __table_args__ = (
        CheckConstraint(
            "discount_value > 0", name="ck_campaigns_discount_positive"
        ),
        CheckConstraint(
            "max_issuances IS NULL OR max_issuances > 0",
            name="ck_campaigns_max_issuances_positive",
        ),
        CheckConstraint("issued_count >= 0", name="ck_campaigns_issued_nonneg"),
        CheckConstraint("ends_at > starts_at", name="ck_campaigns_ends_after_starts"),
        CheckConstraint(
            "program_form IN ('giam_gia','tang_kem','may_rui_quay_so',"
            "'may_rui_truc_tiep','khach_hang_thuong_xuyen')",
            name="ck_campaigns_program_form",
        ),
        CheckConstraint(
            "approval_status IN ('draft','pending_approval','auto_approved',"
            "'approved','rejected','revision_requested')",
            name="ck_campaigns_approval_status",
        ),
        CheckConstraint(
            "approval_tier IN ('none','notify_so_ct','dang_ky_so_ct','full_dossier')",
            name="ck_campaigns_approval_tier",
        ),
        CheckConstraint("estimated_cost >= 0", name="ck_campaigns_estimated_cost_nonneg"),
        CheckConstraint("realized_cost >= 0", name="ck_campaigns_realized_cost_nonneg"),
        CheckConstraint(
            "service_fee_total >= 0",
            name="ck_campaigns_service_fee_total_nonneg",
        ),
        CheckConstraint(
            "service_fee_status IN ('none','estimated','invoiced','paid')",
            name="ck_campaigns_service_fee_status",
        ),
        CheckConstraint(
            "program_form NOT IN ('may_rui_quay_so','may_rui_truc_tiep') "
            "OR approval_tier IN ('dang_ky_so_ct','full_dossier')",
            name="ck_campaigns_may_rui_tier",
        ),
        CheckConstraint(
            "approval_status <> 'rejected' OR ("
            "rejection_reason IS NOT NULL AND reviewed_at IS NOT NULL "
            "AND reviewed_by_user_id IS NOT NULL)",
            name="ck_campaigns_rejected_needs_reason",
        ),
        CheckConstraint(
            "source NOT IN ('signup','birthday') OR template_id IS NOT NULL",
            name="ck_campaigns_template_required_for_system_source",
        ),
        Index("ix_campaigns_partner_active", "partner_id", "is_active"),
        Index(
            "ix_campaigns_pending_approval",
            "partner_id",
            "created_at",
            postgresql_where=text(
                "approval_status = 'pending_approval' AND deleted_at IS NULL"
            ),
        ),
        Index(
            "ix_campaigns_post_report_due",
            "post_report_due_at",
            postgresql_where=text(
                "post_report_submitted_at IS NULL "
                "AND approval_tier IN ('notify_so_ct','dang_ky_so_ct','full_dossier')"
            ),
        ),
        Index(
            "ix_campaigns_active_approved",
            "partner_id",
            "starts_at",
            "ends_at",
            postgresql_where=text(
                "approval_status IN ('auto_approved','approved') "
                "AND is_active = TRUE AND deleted_at IS NULL"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("partners.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    terms: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    usage_guide: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    support_contact: Mapped[str | None] = mapped_column(String(500), nullable=True)
    discount_type: Mapped[DiscountType] = mapped_column(
        String(20), nullable=False
    )
    discount_value: Mapped[int] = mapped_column(Integer, nullable=False)
    min_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_discount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_tier_id: Mapped[int | None] = mapped_column(
        ForeignKey("tiers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    max_issuances: Mapped[int | None] = mapped_column(Integer, nullable=True)
    issued_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source: Mapped[CampaignSource] = mapped_column(
        String(20),
        default=CampaignSource.MANUAL,
        nullable=False,
    )

    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaign_templates.id", ondelete="RESTRICT"), nullable=True
    )
    template_version_snapshot: Mapped[int | None] = mapped_column(Integer, nullable=True)

    program_form: Mapped[str] = mapped_column(String(32), nullable=False)
    approval_status: Mapped[str] = mapped_column(String(30), nullable=False)
    approval_tier: Mapped[str] = mapped_column(String(30), nullable=False)

    estimated_cost: Mapped[int] = mapped_column(BigInteger, nullable=False)
    realized_cost: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    authorization_id: Mapped[int | None] = mapped_column(
        ForeignKey("partner_authorizations.id", ondelete="SET NULL"),
        nullable=True,
    )
    service_fee_total: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0
    )
    service_fee_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=ServiceFeeStatus.NONE.value
    )

    ops_filing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    post_report_due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    post_report_submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
