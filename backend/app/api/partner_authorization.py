"""API merchant Phase 7 — xem uỷ quyền + thu hồi.

- `GET /partner/authorizations` — list uỷ quyền của partner.
- `GET /partner/authorizations/{id}` — detail (kèm signature_payload).
- `POST /partner/authorizations/{id}/revoke` — thu hồi. Guarded bởi
  `campaigns.ops_filing_started_at IS NULL AND approval_status != 'approved'`.
  Sau ops_start → 409 code `REVOKE_BLOCKED_OPS_STARTED`.

Tất cả endpoint yêu cầu owner trong partner (`require_owner_in_partner`) —
staff không được quyết định pháp lý.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user, get_partner_id, require_owner_in_partner
from app.models.partner_staff import PartnerStaffRole
from app.models.user import User
from app.schemas.partner_authorization import (
    AuthorizationRevokeRequest,
    PartnerAuthorizationResponse,
    PartnerAuthorizationSummaryResponse,
)
from app.services.partner_authorization_service import (
    AuthorizationAlreadyRevokedError,
    AuthorizationNotFoundError,
    RevokeBlockedOpsStartedError,
    PartnerAuthorizationService,
)


router = APIRouter(tags=["partner-authorization"])


@router.get(
    "/partner/authorizations",
    response_model=list[PartnerAuthorizationSummaryResponse],
)
async def list_authorizations(
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> list[PartnerAuthorizationSummaryResponse]:
    rows = await PartnerAuthorizationService(db).list_for_partner(partner_id)
    return [PartnerAuthorizationSummaryResponse.model_validate(r) for r in rows]


@router.get(
    "/partner/authorizations/{auth_id}",
    response_model=PartnerAuthorizationResponse,
)
async def get_authorization(
    auth_id: int,
    partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> PartnerAuthorizationResponse:
    try:
        record = await PartnerAuthorizationService(db).get_for_partner(
            partner_id=partner_id, auth_id=auth_id
        )
    except AuthorizationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return PartnerAuthorizationResponse.model_validate(record)


@router.post(
    "/partner/authorizations/{auth_id}/revoke",
    response_model=PartnerAuthorizationResponse,
)
async def revoke_authorization(
    auth_id: int,
    body: AuthorizationRevokeRequest,
    partner_id: int = Depends(get_partner_id),
    user: User = Depends(get_current_user),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> PartnerAuthorizationResponse:
    try:
        record = await PartnerAuthorizationService(db).revoke(
            partner_id=partner_id,
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
    return PartnerAuthorizationResponse.model_validate(record)

