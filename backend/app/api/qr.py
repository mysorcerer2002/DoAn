"""QR API endpoints — /member/qr + /member/checkin."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user, get_optional_user
from app.core.limiter import limiter
from app.core.qr import verify_shop_token
from app.models.membership import Membership
from app.models.partner import Partner, PartnerStatus
from app.models.user import User
from app.schemas.qr import CheckinResponse, QrTokenResponse
from app.services.qr_service import QrService

router = APIRouter(prefix="/member", tags=["member"])


@router.get("/qr", response_model=QrTokenResponse)
@limiter.limit("20/minute")
async def get_member_qr(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QrTokenResponse:
    """Sign QR JWT cho khách. Frontend gọi mỗi 55s để refresh."""
    service = QrService(db)
    result = await service.issue_qr_for_user(current_user.id)
    return QrTokenResponse(**result)


@router.get("/checkin", response_model=CheckinResponse)
@limiter.limit("60/minute")
async def checkin_qr_shop(
    request: Request,
    partner_slug: str = Query(..., alias="partner"),
    shop_token: str = Query(..., min_length=16, max_length=16),
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> CheckinResponse:
    """Khách quét QR shop (deeplink) → verify HMAC token → trả thông tin shop.

    Nếu user đã đăng nhập VÀ là member của shop, trả `is_member=True` + membership_id
    để frontend redirect tới trang chủ thành viên thay vì trang join.
    """
    partner = await db.scalar(
        select(Partner).where(
            Partner.slug == partner_slug, Partner.status == PartnerStatus.ACTIVE
        )
    )
    if partner is None:
        raise HTTPException(status_code=404, detail="Shop not found")

    if not verify_shop_token(partner.id, shop_token):
        raise HTTPException(status_code=401, detail="Invalid shop token")

    is_member = False
    membership_id: int | None = None
    if current_user is not None:
        membership = await db.scalar(
            select(Membership).where(
                Membership.partner_id == partner.id,
                Membership.user_id == current_user.id,
            )
        )
        if membership is not None:
            is_member = True
            membership_id = membership.id

    return CheckinResponse(
        partner_id=partner.id,
        partner_slug=partner.slug,
        partner_name=partner.name,
        is_member=is_member,
        membership_id=membership_id,
    )
