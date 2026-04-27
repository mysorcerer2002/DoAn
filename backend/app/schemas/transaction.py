from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.transaction import TransactionMethod


class CreateManualTransactionRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20)
    gross_amount: int = Field(gt=0, le=100_000_000)
    note: str | None = Field(default=None, max_length=1000)
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
    gross_amount: int
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
    new_balance: int  # Global wallet sau khi cộng điểm
    new_lifetime_earned: int  # Per-shop tier metric sau khi cộng điểm
    new_tier_id: int | None
    new_tier_name: str | None
    tier_upgraded: bool


class CreateQrCustomerTransactionRequest(BaseModel):
    """Tạo giao dịch từ QR scan — staff quét QR khách."""
    qr_payload: str = Field(min_length=1, max_length=500)
    gross_amount: int = Field(gt=0, le=100_000_000)
    note: str | None = Field(default=None, max_length=1000)
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


class NoMembershipResponse(BaseModel):
    """Trả về khi khách chưa là thành viên."""
    user_id: int
    phone: str | None
    full_name: str | None
    is_member: bool = False


class CustomerLookupResponse(BaseModel):
    """Lookup khách trước khi tích điểm. Phone: found=False nếu chưa có user (sẽ auto-create). QR: 4xx nếu invalid."""
    found: bool
    user_id: int | None = None
    phone: str | None = None
    full_name: str | None = None
    email: str | None = None
    points_balance: int | None = None
    is_member: bool = False
    is_active: bool | None = None  # None khi chưa là member; True/False khi đã có membership
    lifetime_earned: int | None = None
    current_tier_name: str | None = None


# ── C2: GET list/detail + PATCH ───────────────────────────────────────────────


class TransactionListItem(BaseModel):
    id: int
    created_at: datetime
    receipt_code: str | None
    membership_display_name: str
    gross_amount: int
    net_amount: int
    points_earned: int
    method: str

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    items: list[TransactionListItem]
    total: int
    page: int
    page_size: int


class TransactionDetailResponse(TransactionListItem):
    note: str | None


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
