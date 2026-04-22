"""API endpoints Phase 6 — flow enroll campaign cho merchant.

- GET `/merchant/campaign-templates` — list template active.
- POST `/merchant/campaigns/enroll/preview` — preview cost + fee + auth doc.
- POST `/merchant/authorizations/request-otp` — gửi OTP email.
- POST `/merchant/authorizations/sign` — verify OTP + tạo chain entity.

Tất cả yêu cầu owner trong tenant (`require_owner_in_tenant`) — staff không
được ký uỷ quyền pháp lý.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user, get_tenant_id, require_owner_in_tenant
from app.core.email import (
    dev_code_leak_enabled,
    mask_email,
    send_otp_email,
)
from app.models.tenant_staff import TenantStaffRole
from app.models.user import User
from app.models.verification_code import VerificationCodePurpose
from app.schemas.campaign_enrollment import (
    AuthorizationOtpRequest,
    AuthorizationOtpResponse,
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
    form_commitment,
)
from app.services.campaign_template_service import CampaignTemplateService
from app.services.verification_code_service import (
    InvalidCodeError,
    VerificationCodeService,
)


router = APIRouter(tags=["merchant-enrollment"])


@router.get(
    "/merchant/campaign-templates",
    response_model=list[CampaignTemplatePublicResponse],
)
async def list_merchant_templates(
    _tenant_id: int = Depends(get_tenant_id),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[CampaignTemplatePublicResponse]:
    rows = await CampaignTemplateService(db).list_templates(is_active=True)
    return [CampaignTemplatePublicResponse.model_validate(r) for r in rows]


@router.post(
    "/merchant/campaigns/enroll/preview",
    response_model=CampaignEnrollPreviewResponse,
)
async def preview_enrollment(
    form: EnrollFormInput,
    tenant_id: int = Depends(get_tenant_id),
    user: User = Depends(get_current_user),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> CampaignEnrollPreviewResponse:
    try:
        return await CampaignEnrollmentService(db).preview(
            tenant_id=tenant_id, user_id=user.id, form=form
        )
    except TemplateInvalidError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FormValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/merchant/authorizations/request-otp",
    response_model=AuthorizationOtpResponse,
)
async def request_authorization_otp(
    body: AuthorizationOtpRequest,
    tenant_id: int = Depends(get_tenant_id),
    user: User = Depends(get_current_user),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> AuthorizationOtpResponse:
    # Validate form + preview trước khi phát OTP — tránh user nhận code rồi
    # mới biết form sai cap.
    try:
        await CampaignEnrollmentService(db).preview(
            tenant_id=tenant_id, user_id=user.id, form=body.form
        )
    except TemplateInvalidError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FormValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not user.email:
        raise HTTPException(
            status_code=400,
            detail="Tài khoản owner chưa có email, không gửi OTP được",
        )

    # Bind OTP vào hash form cụ thể — sign sẽ fail nếu form bị tamper
    # giữa request-otp và sign.
    code = await VerificationCodeService(db).create_code(
        user_id=user.id,
        purpose=VerificationCodePurpose.AUTHORIZATION_SIGN,
        context_hash=form_commitment(body.form),
    )
    await db.commit()

    await send_otp_email(
        to_email=user.email,
        code=code,
        purpose="authorization_sign",
    )

    return AuthorizationOtpResponse(
        email_masked=mask_email(user.email),
        ttl_minutes=VerificationCodeService.TTL_MINUTES,
        dev_code=code if dev_code_leak_enabled() else None,
    )


@router.post(
    "/merchant/authorizations/sign",
    response_model=AuthorizationSignResponse,
    status_code=201,
)
async def sign_authorization(
    body: AuthorizationSignRequest,
    request: Request,
    tenant_id: int = Depends(get_tenant_id),
    user: User = Depends(get_current_user),
    _role: TenantStaffRole = Depends(require_owner_in_tenant),
    db: AsyncSession = Depends(get_db),
) -> AuthorizationSignResponse:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    try:
        return await CampaignEnrollmentService(db).sign_and_enroll(
            tenant_id=tenant_id,
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
    except InvalidCodeError:
        raise HTTPException(
            status_code=400,
            detail="OTP không hợp lệ, đã hết hạn, đã dùng, hoặc form đã bị đổi",
        )
