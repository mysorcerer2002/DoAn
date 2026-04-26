"""Pydantic schemas cho QR endpoints."""

from pydantic import BaseModel


class CheckinResponse(BaseModel):
    """Response từ GET /member/checkin — thông tin shop + membership status."""

    partner_id: int
    partner_slug: str
    partner_name: str
    is_member: bool
    membership_id: int | None
