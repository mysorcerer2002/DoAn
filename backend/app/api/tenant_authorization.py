"""API merchant Phase 7 — xem uỷ quyền + thu hồi + xem phí dịch vụ.

- `GET /merchant/authorizations` — list uỷ quyền của tenant.
- `GET /merchant/authorizations/{id}` — detail (kèm signature_payload).
- `POST /merchant/authorizations/{id}/revoke` — thu hồi. Guarded bởi
  `campaigns.ops_filing_started_at IS NULL AND approval_status != 'approved'`.
  Sau ops_start → 409 code `REVOKE_BLOCKED_OPS_STARTED`.
- `GET /merchant/campaigns/{id}/service-fees` — list phí dịch vụ của 1 campaign.

Tất cả endpoint yêu cầu owner trong tenant (`require_owner_in_tenant`) —
staff không được quyết định pháp lý.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import get_current_user, get_tenant_id, require_owner_in_tenant
from app.models.tenant_staff import TenantStaffRole
from app.models.user import User
from app.schemas.tenant_authorization import (
    AuthorizationRevokeRequest,
    CampaignServiceFeeResponse,
    TenantAuthorizationResponse,
    TenantAuthorizationSummaryResponse,
)
from app.services.campaign_fee_service import CampaignFeeService
from app.services.tenant_authorization_service import (
    AuthorizationAlreadyRevokedError,
    AuthorizationNotFoundError,
    RevokeBlockedOpsStartedError,
    TenantAuthorizationService,
)


router = APIRouter(tags=["merchant-authorization"])


@router.get(
    "/merchant/authorizations",
    response_model=list[TenantAuthorizationSummaryResponse],
)
async def list_authorizations(
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[TenantAuthorizationSummaryResponse]:
    rows = await TenantAuthorizationService(db).list_for_tenant(tenant_id)
    return [TenantAuthorizationSummaryResponse.model_validate(r) for r in rows]


@router.get(
    "/merchant/authorizations/{auth_id}",
    response_model=TenantAuthorizationResponse,
)
async def get_authorization(
    auth_id: int,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> TenantAuthorizationResponse:
    try:
        record = await TenantAuthorizationService(db).get_for_tenant(
            tenant_id=tenant_id, auth_id=auth_id
        )
    except AuthorizationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return TenantAuthorizationResponse.model_validate(record)


@router.post(
    "/merchant/authorizations/{auth_id}/revoke",
    response_model=TenantAuthorizationResponse,
)
async def revoke_authorization(
    auth_id: int,
    body: AuthorizationRevokeRequest,
    tenant_id: int = Depends(get_tenant_id),
    user: User = Depends(get_current_user),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> TenantAuthorizationResponse:
    try:
        record = await TenantAuthorizationService(db).revoke(
            tenant_id=tenant_id,
            auth_id=auth_id,
            user_id=user.id,
            reason=body.reason,
        )
    except AuthorizationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AuthorizationAlreadyRevokedError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except RevokeBlockedOpsStartedError as e:
        # Code riêng cho FE parse — section 9 AC#8.
        raise HTTPException(
            status_code=409,
            detail={
                "code": "REVOKE_BLOCKED_OPS_STARTED",
                "message": str(e),
            },
        )

    await db.commit()
    # Không gọi db.refresh — record đã có đủ field sau flush (service set
    # revoked_at + revoked_reason trong-memory). Tránh 500 nếu refresh fail
    # trong khi DB đã persist.
    return TenantAuthorizationResponse.model_validate(record)


@router.get(
    "/merchant/campaigns/{campaign_id}/service-fees",
    response_model=list[CampaignServiceFeeResponse],
)
async def list_campaign_service_fees(
    campaign_id: int,
    tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[CampaignServiceFeeResponse]:
    """Trả list rỗng khi `SERVICE_FEE_ENABLED=False` (đồ án)."""
    settings = get_settings()
    if not settings.service_fee_enabled:
        return []

    rows = await CampaignFeeService(db).list_for_campaign(
        tenant_id=tenant_id, campaign_id=campaign_id
    )
    return [CampaignServiceFeeResponse.model_validate(r) for r in rows]
