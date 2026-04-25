from datetime import datetime

from pydantic import BaseModel

from app.models.point_ledger import LedgerReason, LedgerRefType


class LedgerEntryResponse(BaseModel):
    id: int
    delta: int
    reason: LedgerReason
    ref_type: LedgerRefType
    ref_id: int | None
    balance_after: int
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReconcileResponse(BaseModel):
    user_id: int
    expected_balance: int
    actual_balance: int
    is_consistent: bool
    diff: int
