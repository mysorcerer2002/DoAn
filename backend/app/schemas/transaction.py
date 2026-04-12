from datetime import datetime

from pydantic import BaseModel, Field

from app.models.transaction import TransactionMethod


class CreateManualTransactionRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20)
    gross_amount: int = Field(gt=0, le=100_000_000)
    note: str | None = Field(default=None, max_length=1000)


class TransactionResponse(BaseModel):
    id: int
    tenant_id: int
    membership_id: int
    staff_id: int
    gross_amount: int
    voucher_id: int | None
    voucher_discount_amount: int | None
    net_amount: int
    points_earned: int
    method: TransactionMethod
    note: str | None
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
