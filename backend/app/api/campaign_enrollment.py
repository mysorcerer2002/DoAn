"""API endpoints Phase 6 — flow enroll campaign cho đối tác.

- GET `/partner/campaign-templates` — list template active.
- POST `/partner/campaigns/enroll/preview` — preview cost + fee + auth doc.
- POST `/partner/authorizations/request-otp` — gửi OTP email.
- POST `/partner/authorizations/sign` — verify OTP + tạo chain entity.

Tất cả yêu cầu owner trong partner (`require_owner_in_partner`) — staff không
được ký uỷ quyền pháp lý.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user, get_partner_id, require_owner_in_partner
from app.models.partner_staff import PartnerStaffRole
from app.models.user import User
from app.schemas.campaign_enrollment import (
    AuthorizationSignRequest,
    AuthorizationSignResponse,
    CampaignEnrollPreviewResponse,
    CampaignTemplatePublicResponse,
    EnrollFormInput,
)
from app.services.campaign_enrollment_service import (
    CampaignEnrollmentService,
    ConsentRequiredError,
    EnrollmentError,
    FormValidationError,
    TemplateInvalidError,
)
from app.services.campaign_template_service import CampaignTemplateService


router = APIRouter(tags=["merchant-enrollment"])


@router.get(
    "/partner/campaign-templates",
    response_model=list[CampaignTemplatePublicResponse],
)
async def list_merchant_templates(
    _partner_id: int = Depends(get_partner_id),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> list[CampaignTemplatePublicResponse]:
    # Chỉ trả template source='manual' — shop không được enroll template
    # auto_cron (birthday/welcome) vì các template này do cron tự issue
    # voucher, không qua flow ký uỷ quyền pháp lý.
    rows = await CampaignTemplateService(db).list_templates(
        source="manual", is_active=True
    )
    return [CampaignTemplatePublicResponse.model_validate(r) for r in rows]


@router.post(
    "/partner/campaigns/enroll/preview",
    response_model=CampaignEnrollPreviewResponse,
)
async def preview_enrollment(
    form: EnrollFormInput,
    partner_id: int = Depends(get_partner_id),
    user: User = Depends(get_current_user),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> CampaignEnrollPreviewResponse:
    try:
        return await CampaignEnrollmentService(db).preview(
            partner_id=partner_id, user_id=user.id, form=form
        )
    except TemplateInvalidError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FormValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/partner/authorizations/sign",
    response_model=AuthorizationSignResponse,
    status_code=201,
)
async def sign_authorization(
    body: AuthorizationSignRequest,
    request: Request,
    partner_id: int = Depends(get_partner_id),
    user: User = Depends(get_current_user),
    _role: PartnerStaffRole = Depends(require_owner_in_partner),
    db: AsyncSession = Depends(get_db),
) -> AuthorizationSignResponse:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    try:
        return await CampaignEnrollmentService(db).sign_and_enroll(
            partner_id=partner_id,
            user_id=user.id,
            form=body.form,
            client_ip=client_ip,
            user_agent=user_agent,
            otp_code=body.otp_code,
            consent_checked=body.consent_checked,
        )
    except TemplateInvalidError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FormValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConsentRequiredError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EnrollmentError as e:
        # Include duplicate-pending campaign (partial unique), tenant/user
        # not found, etc.
        raise HTTPException(status_code=409, detail=str(e))
