"""QR API endpoints — /member/qr + /member/checkin."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.core.qr import verify_shop_token
from app.models.membership import Membership
from app.models.tenant import Tenant, TenantStatus
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
    tenant_slug: str = Query(..., alias="tenant"),
    shop_token: str = Query(..., min_length=16, max_length=16),
    db: AsyncSession = Depends(get_db),
) -> CheckinResponse:
    """Khách quét QR shop (deeplink) → verify HMAC token → trả thông tin shop."""
    tenant = await db.scalar(
        select(Tenant).where(
            Tenant.slug == tenant_slug, Tenant.status == TenantStatus.ACTIVE
        )
    )
    if tenant is None:
        raise HTTPException(status_code=404, detail="Shop not found")

    if not verify_shop_token(tenant.id, shop_token):
        raise HTTPException(status_code=401, detail="Invalid shop token")

    return CheckinResponse(
        tenant_id=tenant.id,
        tenant_slug=tenant.slug,
        tenant_name=tenant.name,
        is_member=False,
        membership_id=None,
    )
