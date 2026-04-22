"""Integration tests — CampaignEnrollmentService: preview + sign_and_enroll.

Phase 16 plan voucher rebuild v2.2. Dùng db_session fixture (testcontainers).
Không có partial-unique `uq_campaigns_tenant_template_active_pending` vì đó là
migration-only constraint, Base.metadata.create_all không tạo nó.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.models.campaign_template import CampaignTemplate
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.models.verification_code import VerificationCodePurpose
from app.schemas.campaign_enrollment import EnrollFormInput
from app.services.campaign_enrollment_service import (
    CampaignEnrollmentService,
    ConsentRequiredError,
    FormValidationError,
    form_commitment,
)
from app.services.verification_code_service import (
    InvalidCodeError,
    VerificationCodeService,
)


# ---------------------------------------------------------------------------
# Setup helper
# ---------------------------------------------------------------------------

async def _setup(db_session):
    """Tạo owner + tenant + template cố định."""
    owner = User(email="enroll_owner@test.com", password_hash="x", is_active=True)
    db_session.add(owner)
    await db_session.flush()

    tenant = Tenant(
        name="Enroll Shop",
        slug="enroll-shop",
        owner_user_id=owner.id,
        status=TenantStatus.ACTIVE,
        settings={},
    )
    db_session.add(tenant)
    await db_session.flush()

    tpl = CampaignTemplate(
        code="tpl-fixed-small",
        name="Fixed Small",
        description=None,
        source="manual",
        program_form="giam_gia",
        discount_type="fixed",
        default_usage_guide=None,
        default_support_contact=None,
        default_terms=None,
        max_discount_percent_cap=None,
        max_discount_value_cap=None,
        max_discount_fixed_cap=20_000,
        min_order_floor=0,
        max_issuances_cap=200,
        max_duration_days=None,
        min_voucher_ttl_days=7,
        max_voucher_ttl_days=90,
        version=1,
        is_active=True,
    )
    db_session.add(tpl)
    await db_session.flush()

    return owner, tenant, tpl


def _base_form(template_id: int, discount_value: int, max_issuances: int) -> EnrollFormInput:
    now = datetime.now(timezone.utc)
    return EnrollFormInput(
        template_id=template_id,
        name="Test Campaign",
        discount_value=discount_value,
        max_issuances=max_issuances,
        starts_at=now,
        ends_at=now + timedelta(days=7),
    )


# ---------------------------------------------------------------------------
# preview — tier và estimated_cost
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_preview_auto_tier_for_small_fixed(db_session):
    """disc=10_000, issuances=10 → cost=100_000 ≤ 500_000 → tier=none."""
    owner, tenant, tpl = await _setup(db_session)
    svc = CampaignEnrollmentService(db_session)
    form = _base_form(tpl.id, discount_value=10_000, max_issuances=10)

    result = await svc.preview(tenant_id=tenant.id, user_id=owner.id, form=form)

    assert result.approval_tier == "none"
    assert result.estimated_cost == 100_000


@pytest.mark.asyncio
async def test_preview_notify_tier_for_medium_fixed(db_session):
    """disc=10_000, issuances=100 → cost=1_000_000 → tier=notify_so_ct."""
    owner, tenant, tpl = await _setup(db_session)
    svc = CampaignEnrollmentService(db_session)
    form = _base_form(tpl.id, discount_value=10_000, max_issuances=100)

    result = await svc.preview(tenant_id=tenant.id, user_id=owner.id, form=form)

    assert result.approval_tier == "notify_so_ct"
    assert result.estimated_cost == 1_000_000


@pytest.mark.asyncio
async def test_preview_full_dossier_tier_for_large_fixed(db_session):
    """disc=50_000, issuances=500 → cost=25_000_000 > 2_000_000 → full_dossier."""
    owner, tenant, _ = await _setup(db_session)

    # Template lớn hơn cho bài này
    tpl_large = CampaignTemplate(
        code="tpl-fixed-large",
        name="Fixed Large",
        description=None,
        source="manual",
        program_form="giam_gia",
        discount_type="fixed",
        default_usage_guide=None,
        default_support_contact=None,
        default_terms=None,
        max_discount_percent_cap=None,
        max_discount_value_cap=None,
        max_discount_fixed_cap=50_000,
        min_order_floor=0,
        max_issuances_cap=500,
        max_duration_days=None,
        min_voucher_ttl_days=7,
        max_voucher_ttl_days=90,
        version=1,
        is_active=True,
    )
    db_session.add(tpl_large)
    await db_session.flush()

    svc = CampaignEnrollmentService(db_session)
    form = _base_form(tpl_large.id, discount_value=50_000, max_issuances=500)

    result = await svc.preview(tenant_id=tenant.id, user_id=owner.id, form=form)

    assert result.approval_tier == "full_dossier"
    assert result.estimated_cost == 25_000_000


@pytest.mark.asyncio
async def test_preview_percent_requires_max_discount_cap(db_session):
    """percent template với max_discount_value_cap=100_000; form max_discount=200_000 → FormValidationError."""
    owner, tenant, _ = await _setup(db_session)

    tpl_pct = CampaignTemplate(
        code="tpl-percent",
        name="Percent",
        description=None,
        source="manual",
        program_form="giam_gia",
        discount_type="percent",
        default_usage_guide=None,
        default_support_contact=None,
        default_terms=None,
        max_discount_percent_cap=50,
        max_discount_value_cap=100_000,
        max_discount_fixed_cap=None,
        min_order_floor=0,
        max_issuances_cap=200,
        max_duration_days=None,
        min_voucher_ttl_days=7,
        max_voucher_ttl_days=90,
        version=1,
        is_active=True,
    )
    db_session.add(tpl_pct)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    form = EnrollFormInput(
        template_id=tpl_pct.id,
        name="Pct Camp",
        discount_value=20,
        max_discount=200_000,  # vượt cap 100_000
        starts_at=now,
        ends_at=now + timedelta(days=7),
    )
    svc = CampaignEnrollmentService(db_session)

    with pytest.raises(FormValidationError) as exc_info:
        await svc.preview(tenant_id=tenant.id, user_id=owner.id, form=form)

    assert "max_discount" in str(exc_info.value)


@pytest.mark.asyncio
async def test_preview_rejects_ends_before_starts(db_session):
    """ends_at <= starts_at → FormValidationError."""
    owner, tenant, tpl = await _setup(db_session)
    svc = CampaignEnrollmentService(db_session)

    now = datetime.now(timezone.utc)
    form = EnrollFormInput(
        template_id=tpl.id,
        name="Bad Dates",
        discount_value=5_000,
        starts_at=now + timedelta(days=5),
        ends_at=now + timedelta(days=1),  # ends before starts
    )

    with pytest.raises(FormValidationError):
        await svc.preview(tenant_id=tenant.id, user_id=owner.id, form=form)


@pytest.mark.asyncio
async def test_preview_rejects_discount_above_template_cap(db_session):
    """discount_value=30_000 > max_discount_fixed_cap=20_000 → FormValidationError."""
    owner, tenant, tpl = await _setup(db_session)
    svc = CampaignEnrollmentService(db_session)
    form = _base_form(tpl.id, discount_value=30_000, max_issuances=10)

    with pytest.raises(FormValidationError):
        await svc.preview(tenant_id=tenant.id, user_id=owner.id, form=form)


@pytest.mark.asyncio
async def test_preview_rejects_max_issuances_above_cap(db_session):
    """max_issuances=300 > max_issuances_cap=200 → FormValidationError."""
    owner, tenant, tpl = await _setup(db_session)
    svc = CampaignEnrollmentService(db_session)
    form = _base_form(tpl.id, discount_value=10_000, max_issuances=300)

    with pytest.raises(FormValidationError):
        await svc.preview(tenant_id=tenant.id, user_id=owner.id, form=form)


# ---------------------------------------------------------------------------
# sign_and_enroll — thành công
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sign_and_enroll_auto_approved_on_tier_none(db_session):
    """tier=none → campaign auto_approved sau OTP hợp lệ."""
    owner, tenant, tpl = await _setup(db_session)

    form = _base_form(tpl.id, discount_value=10_000, max_issuances=10)
    ctx_hash = form_commitment(form)

    vc_svc = VerificationCodeService(db_session)
    code = await vc_svc.create_code(
        user_id=owner.id,
        purpose=VerificationCodePurpose.AUTHORIZATION_SIGN,
        context_hash=ctx_hash,
    )
    await db_session.commit()

    svc = CampaignEnrollmentService(db_session)
    response = await svc.sign_and_enroll(
        tenant_id=tenant.id,
        user_id=owner.id,
        form=form,
        client_ip="127.0.0.1",
        user_agent="pytest",
        otp_code=code,
        consent_checked=True,
    )

    assert response.approval_status == "auto_approved"
    assert response.approval_tier == "none"
    assert response.campaign_id is not None
    assert response.authorization_id is not None


@pytest.mark.asyncio
async def test_sign_and_enroll_pending_for_notify_tier(db_session):
    """cost 1_000_000 → tier=notify_so_ct → approval_status=pending_approval."""
    owner, tenant, tpl = await _setup(db_session)

    form = _base_form(tpl.id, discount_value=10_000, max_issuances=100)
    ctx_hash = form_commitment(form)

    vc_svc = VerificationCodeService(db_session)
    code = await vc_svc.create_code(
        user_id=owner.id,
        purpose=VerificationCodePurpose.AUTHORIZATION_SIGN,
        context_hash=ctx_hash,
    )
    await db_session.commit()

    svc = CampaignEnrollmentService(db_session)
    response = await svc.sign_and_enroll(
        tenant_id=tenant.id,
        user_id=owner.id,
        form=form,
        client_ip="127.0.0.1",
        user_agent="pytest",
        otp_code=code,
        consent_checked=True,
    )

    assert response.approval_status == "pending_approval"
    assert response.approval_tier == "notify_so_ct"


# ---------------------------------------------------------------------------
# sign_and_enroll — validation guards
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sign_requires_consent_checked(db_session):
    """consent_checked=False → ConsentRequiredError trước khi check OTP."""
    owner, tenant, tpl = await _setup(db_session)
    form = _base_form(tpl.id, discount_value=10_000, max_issuances=10)
    svc = CampaignEnrollmentService(db_session)

    with pytest.raises(ConsentRequiredError):
        await svc.sign_and_enroll(
            tenant_id=tenant.id,
            user_id=owner.id,
            form=form,
            client_ip=None,
            user_agent=None,
            otp_code="000000",
            consent_checked=False,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mutate_field,mutate_value",
    [
        ("discount_value", 15_000),
        ("name", "Camp B (đã đổi)"),
        ("max_issuances", 20),
    ],
    ids=["discount_value", "name", "max_issuances"],
)
async def test_sign_rejects_tampered_form(db_session, mutate_field, mutate_value):
    """OTP bind form_commitment(formA); sign với formB đổi 1 field → InvalidCodeError.

    Parametrize qua 3 field khác nhau để chứng form_commitment cover toàn bộ form,
    không chỉ 1 field cố định.
    """
    owner, tenant, tpl = await _setup(db_session)

    now = datetime.now(timezone.utc)
    base_kwargs = dict(
        template_id=tpl.id,
        name="Camp A",
        discount_value=10_000,
        max_issuances=10,
        starts_at=now,
        ends_at=now + timedelta(days=7),
    )
    form_a = EnrollFormInput(**base_kwargs)
    form_b_kwargs = {**base_kwargs, mutate_field: mutate_value}
    form_b = EnrollFormInput(**form_b_kwargs)

    vc_svc = VerificationCodeService(db_session)
    code = await vc_svc.create_code(
        user_id=owner.id,
        purpose=VerificationCodePurpose.AUTHORIZATION_SIGN,
        context_hash=form_commitment(form_a),
    )
    await db_session.commit()

    svc = CampaignEnrollmentService(db_session)
    with pytest.raises(InvalidCodeError):
        await svc.sign_and_enroll(
            tenant_id=tenant.id,
            user_id=owner.id,
            form=form_b,  # hash khác form_a
            client_ip=None,
            user_agent=None,
            otp_code=code,
            consent_checked=True,
        )


@pytest.mark.asyncio
async def test_sign_rejects_wrong_otp_code(db_session):
    """otp_code không tồn tại → InvalidCodeError."""
    owner, tenant, tpl = await _setup(db_session)
    form = _base_form(tpl.id, discount_value=10_000, max_issuances=10)
    svc = CampaignEnrollmentService(db_session)

    with pytest.raises(InvalidCodeError):
        await svc.sign_and_enroll(
            tenant_id=tenant.id,
            user_id=owner.id,
            form=form,
            client_ip=None,
            user_agent=None,
            otp_code="999999",  # không tồn tại
            consent_checked=True,
        )
