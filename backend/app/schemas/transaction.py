from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.transaction import TransactionMethod


class CreateManualTransactionRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20)
    gross_amount: int = Field(gt=0, le=100_000_000)
    note: str | None = Field(default=None, max_length=1000)
    voucher_code: str | None = Field(default=None, min_length=8, max_length=8)
    receipt_code: str | None = Field(default=None, max_length=50)

    @field_validator("receipt_code", mode="before")
    @classmethod
    def _normalize_receipt_code(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            if v == "":
                return None
        return v


class TransactionResponse(BaseModel):
    id: int
    partner_id: int
    membership_id: int
    staff_id: int
    gross_amount: int
    voucher_id: int | None
    voucher_discount_amount: int | None
    net_amount: int
    points_earned: int
    method: TransactionMethod
    note: str | None
    receipt_code: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionWithMemberResponse(BaseModel):
    transaction: TransactionResponse
    member_phone: str | None
    member_full_name: str | None
    new_balance: int
    new_total_earned: int
    new_tier_id: int | None
    new_tier_name: str | None
    tier_upgraded: bool
    welcome_voucher_code: str | None = None


class CreateQrCustomerTransactionRequest(BaseModel):
    """Tạo giao dịch từ QR scan — staff quét QR khách."""
    qr_payload: str = Field(min_length=1, max_length=500)
    gross_amount: int = Field(gt=0, le=100_000_000)
    note: str | None = Field(default=None, max_length=1000)


class NoMembershipResponse(BaseModel):
    """Trả về khi khách chưa là thành viên."""
    user_id: int
    phone: str | None
    full_name: str | None
    is_member: bool = False


# ── C2: GET list/detail + PATCH ───────────────────────────────────────────────


class TransactionListItem(BaseModel):
    id: int
    created_at: datetime
    receipt_code: str | None
    membership_display_name: str
    staff_display_name: str | None
    gross_amount: int
    voucher_discount_amount: int | None
    net_amount: int
    points_earned: int
    method: str
    voucher_code: str | None

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    items: list[TransactionListItem]
    total: int
    page: int
    page_size: int


class TransactionDetailResponse(TransactionListItem):
    note: str | None
    legal_discount_ratio: Decimal | None


class TransactionUpdateRequest(BaseModel):
    receipt_code: str | None = Field(default=None, max_length=50)
    note: str | None = None

    @field_validator("receipt_code", mode="before")
    @classmethod
    def _normalize_receipt_code(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            if v == "":
                return None
        return v
