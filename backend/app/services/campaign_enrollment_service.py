"""CampaignEnrollmentService — preview + request-otp + sign.

Phase 6 của plan voucher rebuild v2.2. Shop chọn template, fill instance,
xem nội dung uỷ quyền, ký qua OTP email → hệ thống tạo chain entity:

- Campaign (pending_approval hoặc auto_approved tuỳ tier)
- PartnerAuthorization (signed, with signature_payload JSONB)
- CampaignApprovalEvent (event_type='submitted')

Tier rule (I6 plan, đã có ở CampaignTemplateService.compute_tier_hint):
form-based trước, rồi cost-based.
"""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.campaign import Campaign
from app.models.campaign_approval_event import (
    ApprovalEventType,
    CampaignApprovalEvent,
)
from app.models.campaign_template import CampaignTemplate
from app.models.partner import Partner
from app.models.partner_authorization import PartnerAuthorization
from app.models.user import User
from app.schemas.campaign_enrollment import (
    AuthorizationSignResponse,
    CampaignEnrollPreviewResponse,
    EnrollFormInput,
)
from app.services.campaign_template_service import CampaignTemplateService


class TemplateInvalidError(Exception):
    pass


class FormValidationError(Exception):
    pass


class EnrollmentError(Exception):
    pass


class ConsentRequiredError(Exception):
    pass


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def form_commitment(form: EnrollFormInput) -> str:
    """Hash canonical của form — bind OTP vào form cụ thể.

    `sort_keys=True` + `default=str` (cho datetime) để cùng form luôn cho
    cùng hash bất kể thứ tự key. Dùng ở request-otp + sign để verify
    form không bị đổi giữa 2 bước.
    """
    payload = form.model_dump(mode="json")
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return _sha256_hex(canonical)


def _render_auth_doc(
    *,
    partner: Partner,
    user: User,
    campaign_name: str,
    estimated_cost: int,
    approval_tier: str,
    consent_version: str,
) -> str:
    """Render nội dung văn bản uỷ quyền (Điều 562-569 BLDS 2015)."""
    tier_vi = {
        "none": "không cần nộp hồ sơ Sở Công Thương",
        "notify_so_ct": "thông báo Sở Công Thương (Điều 17 NĐ 81/2018)",
        "dang_ky_so_ct": "đăng ký Sở Công Thương (Điều 19 NĐ 81/2018)",
        "full_dossier": "đăng ký Sở Công Thương kèm hồ sơ đầy đủ (NĐ 81/2018)",
    }.get(approval_tier, approval_tier)

    return (
        f"GIẤY UỶ QUYỀN ĐIỆN TỬ\n"
        f"Phiên bản: {consent_version}\n"
        f"Căn cứ Điều 562-569 Bộ luật Dân sự 2015.\n\n"
        f"Bên uỷ quyền (Bên A): {partner.name} — {partner.address or ''}\n"
        f"Đại diện: {user.full_name or user.email or user.phone or ''}\n\n"
        f"Bên nhận uỷ quyền (Bên B): Công ty TNHH Loyalty Platform\n\n"
        f"1. Phạm vi uỷ quyền: Bên A uỷ quyền Bên B thay mặt thực hiện "
        f"thủ tục {tier_vi} cho chiến dịch khuyến mãi \"{campaign_name}\" "
        f"với ngân sách dự kiến {estimated_cost:,} VND.\n\n"
        f"2. Thời hạn uỷ quyền: Từ ngày ký đến ngày Sở Công Thương xác "
        f"nhận hoàn tất / Bên A thu hồi uỷ quyền (khi chưa ops_filing_started).\n\n"
        f"3. Trách nhiệm Bên B: Chuẩn bị hồ sơ, nộp đúng thời hạn, thông "
        f"báo kết quả; không được uỷ quyền lại cho bên thứ ba.\n\n"
        f"4. Trách nhiệm Bên A: Cung cấp thông tin chính xác, thanh toán "
        f"phí dịch vụ theo hoá đơn; chịu trách nhiệm về nội dung khuyến "
        f"mãi trước pháp luật.\n\n"
        f"5. Phí dịch vụ: Theo bảng giá hiện hành, đã bao gồm VAT 10%.\n\n"
        f"Bằng việc nhập OTP gửi đến email đăng ký và bấm \"Đồng ý\", "
        f"Bên A xác nhận đã đọc, hiểu và đồng ý toàn bộ điều khoản trên."
    )


class CampaignEnrollmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------
    # Validate + compute
    # ------------------------------------------------------------

    async def _load_template(self, template_id: int) -> CampaignTemplate:
        template = await self.db.get(CampaignTemplate, template_id)
        if (
            template is None
            or template.deleted_at is not None
            or not template.is_active
        ):
            raise TemplateInvalidError(
                f"Template {template_id} không tồn tại hoặc đã tắt"
            )
        return template

    def _validate_form(
        self, template: CampaignTemplate, form: EnrollFormInput
    ) -> None:
        """Ép form instance tuân caps từ template."""
        if form.ends_at <= form.starts_at:
            raise FormValidationError("ends_at phải > starts_at")

        if template.max_duration_days is not None:
            duration = (form.ends_at - form.starts_at).days
            if duration > template.max_duration_days:
                raise FormValidationError(
                    f"Thời lượng {duration} ngày vượt cap "
                    f"{template.max_duration_days} ngày"
                )

        if template.min_order_floor and form.min_order < template.min_order_floor:
            raise FormValidationError(
                f"min_order {form.min_order} < floor "
                f"{template.min_order_floor}"
            )

        if (
            template.max_issuances_cap is None
            and form.max_issuances is None
        ):
            # Nếu cả template lẫn form đều không chốt quota → _estimate_cost
            # = 0 → tier='none' auto_approved, bypass kiểm duyệt pháp lý dù
            # thực tế chi phí có thể rất lớn. Ép shop phải điền.
            raise FormValidationError(
                "Campaign phải có max_issuances (số lượng voucher phát hành) "
                "hoặc template phải đặt max_issuances_cap"
            )

        if (
            template.max_issuances_cap is not None
            and form.max_issuances is not None
            and form.max_issuances > template.max_issuances_cap
        ):
            raise FormValidationError(
                f"max_issuances vượt cap {template.max_issuances_cap}"
            )

        if template.discount_type == "percent":
            if template.max_discount_percent_cap is not None and (
                form.discount_value > template.max_discount_percent_cap
            ):
                raise FormValidationError(
                    f"discount_value {form.discount_value}% vượt cap "
                    f"{template.max_discount_percent_cap}%"
                )
            # Percent campaign BẮT BUỘC có trần VND/voucher (form hoặc
            # template) — nếu không, _estimate_cost = 0 → tier=none và
            # auto_approve dù thực tế ngân sách có thể rất lớn, bypass kiểm
            # duyệt pháp lý.
            if (
                form.max_discount is None
                and template.max_discount_value_cap is None
            ):
                raise FormValidationError(
                    "Campaign percent phải có max_discount (trần VND/voucher) "
                    "hoặc template phải đặt max_discount_value_cap"
                )
            if (
                form.max_discount is not None
                and template.max_discount_value_cap is not None
                and form.max_discount > template.max_discount_value_cap
            ):
                raise FormValidationError(
                    f"max_discount {form.max_discount} vượt cap "
                    f"{template.max_discount_value_cap}"
                )
        else:  # fixed
            if (
                template.max_discount_fixed_cap is not None
                and form.discount_value > template.max_discount_fixed_cap
            ):
                raise FormValidationError(
                    f"discount_value {form.discount_value} vượt cap "
                    f"{template.max_discount_fixed_cap}"
                )

    def _estimate_cost(
        self, template: CampaignTemplate, form: EnrollFormInput
    ) -> int:
        """Ước lượng ngân sách tối đa shop chi = per-voucher cap × số lượng."""
        issuances = form.max_issuances or template.max_issuances_cap or 0
        if issuances == 0:
            return 0
        if template.discount_type == "percent":
            per_voucher = form.max_discount or template.max_discount_value_cap or 0
        else:
            per_voucher = form.discount_value
        return int(per_voucher) * int(issuances)

    # ------------------------------------------------------------
    # Public flows
    # ------------------------------------------------------------

    async def preview(
        self,
        *,
        partner_id: int,
        user_id: int,
        form: EnrollFormInput,
    ) -> CampaignEnrollPreviewResponse:
        template = await self._load_template(form.template_id)
        self._validate_form(template, form)

        estimated_cost = self._estimate_cost(template, form)
        approval_tier = CampaignTemplateService.compute_tier_hint(
            template.program_form, estimated_cost
        )

        partner = await self.db.get(Partner, partner_id)
        user = await self.db.get(User, user_id)
        if partner is None or user is None:
            raise EnrollmentError("đối tác/user không tồn tại")

        settings = get_settings()
        auth_doc_text = _render_auth_doc(
            partner=partner,
            user=user,
            campaign_name=form.name,
            estimated_cost=estimated_cost,
            approval_tier=approval_tier,
            consent_version=settings.consent_text_version,
        )

        return CampaignEnrollPreviewResponse(
            template_id=template.id,
            template_version=template.version,
            program_form=template.program_form
            if isinstance(template.program_form, str)
            else template.program_form.value,
            approval_tier=approval_tier,
            estimated_cost=estimated_cost,
            auth_doc_text=auth_doc_text,
            auth_doc_hash=_sha256_hex(auth_doc_text),
            consent_text_version=settings.consent_text_version,
        )

    async def sign_and_enroll(
        self,
        *,
        partner_id: int,
        user_id: int,
        form: EnrollFormInput,
        client_ip: str | None,
        user_agent: str | None,
        otp_code: str,
        consent_checked: bool,
    ) -> AuthorizationSignResponse:
        """Verify OTP + tạo chain entity trong cùng transaction.

        Ordering (C3 plan): campaign TRƯỚC (FK nguồn), authorization TIẾP (ref
        campaign), UPDATE campaign.authorization_id SAU, fee rows + approval
        event CUỐI.
        """
        if not consent_checked:
            raise ConsentRequiredError("Phải tick đồng ý trước khi ký")

        # Re-compute preview để đảm bảo hash + tier không bị tampered.
        preview = await self.preview(
            partner_id=partner_id, user_id=user_id, form=form
        )
        template = await self._load_template(form.template_id)

        # Verify OTP (inline import tránh circular).
        from app.models.verification_code import VerificationCodePurpose
        from app.services.verification_code_service import (
            VerificationCodeService,
        )

        vc = VerificationCodeService(self.db)
        await vc.verify_code(
            user_id=user_id,
            code=otp_code,
            purpose=VerificationCodePurpose.AUTHORIZATION_SIGN,
            context_hash=form_commitment(form),
        )

        settings = get_settings()
        now = datetime.now(timezone.utc)

        # 1. Tạo campaign pending (hoặc auto_approved nếu tier=none).
        auto_approved = preview.approval_tier == "none"
        approval_status = "auto_approved" if auto_approved else "pending_approval"

        template_discount_type = (
            template.discount_type.value
            if hasattr(template.discount_type, "value")
            else template.discount_type
        )
        campaign = Campaign(
            partner_id=partner_id,
            name=form.name,
            description=form.description,
            terms=form.terms,
            usage_guide=form.usage_guide,
            support_contact=form.support_contact,
            discount_type=template_discount_type,
            discount_value=form.discount_value,
            min_order=form.min_order,
            max_discount=form.max_discount,
            target_tier_id=form.target_tier_id,
            max_issuances=form.max_issuances,
            issued_count=0,
            starts_at=form.starts_at,
            ends_at=form.ends_at,
            is_active=True,
            source="manual",
            template_id=form.template_id,
            template_version_snapshot=preview.template_version,
            program_form=preview.program_form,
            approval_status=approval_status,
            approval_tier=preview.approval_tier,
            estimated_cost=preview.estimated_cost,
            realized_cost=0,
            created_by_user_id=user_id,
        )
        if auto_approved:
            campaign.reviewed_at = now
        self.db.add(campaign)
        try:
            await self.db.flush()  # cần id
        except IntegrityError as e:
            await self.db.rollback()
            msg = str(e.orig) if hasattr(e, "orig") else str(e)
            if "uq_campaigns_tenant_template_active_pending" in msg:
                raise EnrollmentError(
                    "Shop đang có 1 campaign pending cho template này. "
                    "Chờ duyệt/huỷ trước khi đăng ký campaign mới."
                )
            raise

        # 2. Tạo authorization record.
        # CHECK: retention_until >= signed_at + INTERVAL '10 years'. Dùng
        # 366*years + 1 để vượt qua năm nhuận; INTERVAL Postgres tính theo
        # lịch chính xác (> 365 * years ngày).
        retention_until = now + timedelta(
            days=366 * settings.auth_retention_years + 1
        )
        signature_payload: dict[str, Any] = {
            "ip": client_ip,
            "user_agent": user_agent,
            "otp_purpose": "authorization_sign",
            "consent_text_version": preview.consent_text_version,
            "doc_hash": preview.auth_doc_hash,
            "template_version": preview.template_version,
            "signed_at_server": now.isoformat(),
        }
        authorization = PartnerAuthorization(
            partner_id=partner_id,
            scope="per_campaign",
            campaign_id=campaign.id,
            document_content_hash=preview.auth_doc_hash,
            signed_by_user_id=user_id,
            signed_at=now,
            signature_method="otp_email",
            signature_payload=signature_payload,
            valid_from=now,
            valid_until=form.ends_at + timedelta(days=90),
            retention_until=retention_until,
        )
        self.db.add(authorization)
        await self.db.flush()

        campaign.authorization_id = authorization.id

        # 3. Audit event. AUTO_APPROVED không phải người ký — actor=None
        # để audit Sở CT không nhầm "owner tự duyệt". SUBMITTED thì actor=
        # chính owner.
        event_type = (
            ApprovalEventType.AUTO_APPROVED.value
            if auto_approved
            else ApprovalEventType.SUBMITTED.value
        )
        self.db.add(
            CampaignApprovalEvent(
                campaign_id=campaign.id,
                event_type=event_type,
                actor_user_id=None if auto_approved else user_id,
                at=now,
                reason=None,
            )
        )

        try:
            await self.db.commit()
        except IntegrityError as e:
            await self.db.rollback()
            msg = str(e.orig) if hasattr(e, "orig") else str(e)
            if "uq_campaigns_tenant_template_active_pending" in msg:
                raise EnrollmentError(
                    "Shop đang có 1 campaign pending cho template này. "
                    "Chờ duyệt/huỷ trước khi đăng ký campaign mới."
                )
            raise
        await self.db.refresh(campaign)
        await self.db.refresh(authorization)

        return AuthorizationSignResponse(
            campaign_id=campaign.id,
            authorization_id=authorization.id,
            approval_status=campaign.approval_status,
            approval_tier=campaign.approval_tier,
        )
