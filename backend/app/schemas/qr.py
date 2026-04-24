"""Pydantic schemas cho QR endpoints."""

from pydantic import BaseModel


class QrTokenResponse(BaseModel):
    """Response từ GET /member/qr — chứa JWT + fallback_code."""

    jwt: str
    exp_at_server: int  # Unix timestamp
    fallback_code: str


class CheckinResponse(BaseModel):
    """Response từ GET /member/checkin — thông tin shop + membership status."""

    partner_id: int
    tenant_slug: str
    tenant_name: str
    is_member: bool
    membership_id: int | None
