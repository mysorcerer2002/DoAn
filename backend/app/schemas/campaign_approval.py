"""DTO cho admin approval queue — Phase 8 plan voucher rebuild v2.2."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PendingCampaignRow(BaseModel):
    # Build thủ công từ tuple `(Campaign, tenant_name)` — không cần
    # from_attributes.
    id: int
    tenant_id: int
    tenant_name: str
    name: str
    program_form: str
    approval_status: str
    approval_tier: str
    estimated_cost: int
    service_fee_total: int
    service_fee_status: str
    starts_at: datetime
    ends_at: datetime
    authorization_id: int | None
    ops_filing_started_at: datetime | None
    created_at: datetime


class AdminCampaignDetailResponse(BaseModel):
    """Chi tiết campaign + metadata ops workflow."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    name: str
    description: str | None
    program_form: str
    approval_status: str
    approval_tier: str
    estimated_cost: int
    realized_cost: int
    service_fee_total: int
    service_fee_status: str
    starts_at: datetime
    ends_at: datetime
    authorization_id: int | None
    ops_filing_started_at: datetime | None
    post_report_due_at: datetime | None
    post_report_submitted_at: datetime | None
    reviewed_at: datetime | None
    reviewed_by_user_id: int | None
    rejection_reason: str | None
    created_at: datetime


class RegulatorySubmissionRequest(BaseModel):
    doc_type: str = Field(
        ..., description="notify_so_ct | dang_ky_so_ct | dieu_le | du_toan | xac_nhan_so_ct | bao_cao_ket_thuc"
    )
    reference_no: str | None = Field(default=None, max_length=120)
    url: str | None = Field(default=None, max_length=500)
    note: str | None = Field(default=None, max_length=2000)
    submitted_at: datetime | None = None


class RegulatorySubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int
    doc_type: str
    reference_no: str | None
    url: str | None
    note: str | None
    submitted_at: datetime
    submitted_by_user_id: int


class RejectCampaignRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=2000)
    acknowledge_used_vouchers: bool = Field(
        default=False,
        description=(
            "Bắt buộc True nếu campaign có voucher status='used'. "
            "Voucher used không bị cancel, nhưng admin phải xác nhận."
        ),
    )


class OverdueReportRow(BaseModel):
    # Build thủ công từ `(Campaign, tenant_name, days_overdue)`.
    id: int
    tenant_id: int
    tenant_name: str
    name: str
    approval_tier: str
    ends_at: datetime
    post_report_due_at: datetime
    days_overdue: int


class ApprovalEventRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int
    event_type: str
    actor_user_id: int | None
    reason: str | None
    at: datetime
