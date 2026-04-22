"""Integration tests — CampaignApprovalService: approve, reject, revoke.

Phase 16 plan voucher rebuild v2.2. Dùng db_session fixture (testcontainers).
Insert trực tiếp để control state — không mất thời gian OTP flow.

NOTE: TenantAuthorization có CHECK:
  - scope='per_campaign' → campaign_id IS NOT NULL
  - retention_until >= signed_at + INTERVAL '10 years'
  - valid_until > valid_from

Strategy: insert campaign với authorization_id=NULL trước (temporary), flush,
insert authorization với campaign_id=campaign.id, flush, rồi update
campaign.authorization_id.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.models.campaign import Campaign
from app.models.campaign_regulatory_submission import CampaignRegulatorySubmission
from app.models.campaign_template import CampaignTemplate
from app.models.membership import Membership
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_authorization import TenantAuthorization
from app.models.user import User
from app.models.voucher import Voucher, VoucherStatus
from app.services.campaign_approval_service import (
    ApprovalGuardFailed,
    CampaignApprovalService,
    InvalidStateError,
    UsedVouchersBlockRejectError,
)
from app.services.tenant_authorization_service import (
    RevokeBlockedOpsStartedError,
    TenantAuthorizationService,
)


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------

async def _create_user(db_session, email: str) -> User:
    user = User(email=email, password_hash="x", is_active=True)
    db_session.add(user)
    await db_session.flush()
    return user


async def _create_membership(db_session, tenant_id: int, user_id: int) -> Membership:
    mem = Membership(
        tenant_id=tenant_id,
        user_id=user_id,
        points_balance=0,
        total_points_earned=0,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(mem)
    await db_session.flush()
    return mem


async def _setup(db_session):
    """
    Tạo: owner + tenant + template + campaign(pending_approval) + authorization.

    Thứ tự insert tuân CHECK constraints:
    1. campaign với authorization_id=NULL
    2. authorization với campaign_id=campaign.id
    3. campaign.authorization_id = authorization.id
    """
    now = datetime.now(timezone.utc)

    owner = await _create_user(db_session, "approval_owner@test.com")

    tenant = Tenant(
        name="Approval Shop",
        slug="approval-shop",
        owner_user_id=owner.id,
        status=TenantStatus.ACTIVE,
        settings={},
    )
    db_session.add(tenant)
    await db_session.flush()

    tpl = CampaignTemplate(
        code="tpl-approval",
        name="Approval Template",
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

    # 1. Campaign trước (authorization_id=NULL tạm thời)
    campaign = Campaign(
        tenant_id=tenant.id,
        name="C1",
        discount_type="fixed",
        discount_value=10_000,
        max_issuances=100,
        issued_count=0,
        starts_at=now - timedelta(hours=1),
        ends_at=now + timedelta(days=7),
        is_active=True,
        source="manual",
        program_form="giam_gia",
        approval_status="pending_approval",
        approval_tier="notify_so_ct",
        estimated_cost=1_000_000,
        realized_cost=0,
        service_fee_total=0,
        service_fee_status="none",
        authorization_id=None,
        created_by_user_id=owner.id,
        template_id=tpl.id,
    )
    db_session.add(campaign)
    await db_session.flush()

    # 2. Authorization tham chiếu campaign
    auth = TenantAuthorization(
        tenant_id=tenant.id,
        scope="per_campaign",
        campaign_id=campaign.id,
        document_content_hash="x" * 64,
        signed_by_user_id=owner.id,
        signed_at=now,
        signature_method="otp_email",
        signature_payload={"ip": "127.0.0.1"},
        valid_from=now,
        valid_until=now + timedelta(days=90),
        retention_until=now + timedelta(days=366 * 10 + 1),
    )
    db_session.add(auth)
    await db_session.flush()

    # 3. Link ngược lại
    campaign.authorization_id = auth.id
    await db_session.flush()

    return owner, tenant, campaign, auth


async def _insert_voucher(
    db_session,
    *,
    tenant_id: int,
    campaign_id: int,
    membership_id: int,
    code: str,
    status: str = "issued",
) -> Voucher:
    """Insert voucher trực tiếp, bypass VoucherService.claim.

    Conftest dùng Base.metadata.create_all nên partial unique index trên
    campaign_issuances (migration-only) không tồn tại → claim() fail ON CONFLICT.
    Test này chỉ cần voucher ở state cụ thể, không test claim logic.
    """
    now = datetime.now(timezone.utc)
    v = Voucher(
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        membership_id=membership_id,
        code=code,
        status=status,
        issue_source="manual",
        discount_snapshot={"discount_type": "fixed", "discount_value": 10_000},
        issued_at=now,
        expires_at=now + timedelta(days=7),
        used_at=now if status == "used" else None,
    )
    db_session.add(v)
    await db_session.flush()
    return v


async def _add_xac_nhan(db_session, campaign_id: int, user_id: int) -> CampaignRegulatorySubmission:
    """Thêm document xac_nhan_so_ct (điều kiện approve)."""
    doc = CampaignRegulatorySubmission(
        campaign_id=campaign_id,
        doc_type="xac_nhan_so_ct",
        reference_no=None,
        url=None,
        note=None,
        submitted_at=datetime.now(timezone.utc),
        submitted_by_user_id=user_id,
    )
    db_session.add(doc)
    await db_session.flush()
    return doc


# ---------------------------------------------------------------------------
# approve — guards
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_approve_guard_requires_xac_nhan_so_ct_submission(db_session):
    """Không có CampaignRegulatorySubmission doc_type=xac_nhan_so_ct → ApprovalGuardFailed."""
    owner, tenant, campaign, auth = await _setup(db_session)
    svc = CampaignApprovalService(db_session)

    with pytest.raises(ApprovalGuardFailed) as exc_info:
        await svc.approve(campaign_id=campaign.id, user_id=owner.id)

    msg = str(exc_info.value).lower()
    assert "xac_nhan_so_ct" in msg or "xác nhận" in msg or "sở ct" in msg.lower()


@pytest.mark.asyncio
async def test_approve_success_with_xac_nhan_so_ct(db_session):
    """Có xac_nhan_so_ct → approve OK, status=approved, post_report_due_at set."""
    owner, tenant, campaign, auth = await _setup(db_session)
    await _add_xac_nhan(db_session, campaign.id, owner.id)

    svc = CampaignApprovalService(db_session)
    result = await svc.approve(campaign_id=campaign.id, user_id=owner.id)

    assert result.approval_status == "approved"
    assert result.reviewed_at is not None
    expected_due = campaign.ends_at + timedelta(days=45)
    # So sánh date-level (không phụ thuộc microsecond)
    assert result.post_report_due_at.date() == expected_due.date()


@pytest.mark.asyncio
async def test_approve_guard_fails_on_revoked_authorization(db_session):
    """authorization.revoked_at != None → ApprovalGuardFailed."""
    owner, tenant, campaign, auth = await _setup(db_session)
    await _add_xac_nhan(db_session, campaign.id, owner.id)

    # Revoke auth trực tiếp
    auth.revoked_at = datetime.now(timezone.utc)
    await db_session.flush()

    svc = CampaignApprovalService(db_session)
    with pytest.raises(ApprovalGuardFailed) as exc_info:
        await svc.approve(campaign_id=campaign.id, user_id=owner.id)

    assert "thu hồi" in str(exc_info.value) or "revoked" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_approve_rejects_wrong_state(db_session):
    """campaign.approval_status='approved' → gọi approve lần 2 → ApprovalGuardFailed."""
    owner, tenant, campaign, auth = await _setup(db_session)
    await _add_xac_nhan(db_session, campaign.id, owner.id)

    svc = CampaignApprovalService(db_session)
    # Lần 1 thành công
    await svc.approve(campaign_id=campaign.id, user_id=owner.id)
    await db_session.flush()

    # Lần 2 phải fail
    with pytest.raises(ApprovalGuardFailed):
        await svc.approve(campaign_id=campaign.id, user_id=owner.id)


@pytest.mark.asyncio
async def test_approve_blocked_from_revision_requested(db_session):
    """approval_status='revision_requested' không phải 'pending_approval' → ApprovalGuardFailed.

    Approve chỉ nhận 'pending_approval' (xem CampaignApprovalService.approve guard a).
    Campaign ở 'revision_requested' phải resubmit thành 'pending_approval' trước khi
    approve được.
    """
    owner, tenant, campaign, auth = await _setup(db_session)
    await _add_xac_nhan(db_session, campaign.id, owner.id)

    campaign.approval_status = "revision_requested"
    await db_session.flush()

    svc = CampaignApprovalService(db_session)
    with pytest.raises(ApprovalGuardFailed) as exc_info:
        await svc.approve(campaign_id=campaign.id, user_id=owner.id)
    assert "revision_requested" in str(exc_info.value)


# ---------------------------------------------------------------------------
# reject — used-voucher guard + cascade cancel
# ---------------------------------------------------------------------------

async def _make_approved_campaign(db_session, owner, tenant, tpl_id: int | None = None):
    """Tạo campaign ở trạng thái 'approved' để VoucherService.claim chấp nhận."""
    now = datetime.now(timezone.utc)

    campaign = Campaign(
        tenant_id=tenant.id,
        name="Approved C",
        discount_type="fixed",
        discount_value=10_000,
        max_issuances=100,
        issued_count=0,
        starts_at=now - timedelta(hours=1),
        ends_at=now + timedelta(days=7),
        is_active=True,
        source="manual",
        program_form="giam_gia",
        approval_status="approved",
        approval_tier="notify_so_ct",
        estimated_cost=1_000_000,
        realized_cost=0,
        service_fee_total=0,
        service_fee_status="none",
        authorization_id=None,
        created_by_user_id=owner.id,
        template_id=tpl_id,
        reviewed_at=now,
        reviewed_by_user_id=owner.id,
    )
    db_session.add(campaign)
    await db_session.flush()

    auth = TenantAuthorization(
        tenant_id=tenant.id,
        scope="per_campaign",
        campaign_id=campaign.id,
        document_content_hash="y" * 64,
        signed_by_user_id=owner.id,
        signed_at=now,
        signature_method="otp_email",
        signature_payload={"ip": "127.0.0.1"},
        valid_from=now,
        valid_until=now + timedelta(days=90),
        retention_until=now + timedelta(days=366 * 10 + 1),
    )
    db_session.add(auth)
    await db_session.flush()

    campaign.authorization_id = auth.id
    await db_session.flush()

    return campaign, auth


@pytest.mark.asyncio
async def test_reject_without_ack_blocked_when_has_used_voucher(db_session):
    """campaign 'approved' với 1 voucher used → reject(ack=False) → UsedVouchersBlockRejectError."""
    owner, tenant, _, _ = await _setup(db_session)
    campaign, auth = await _make_approved_campaign(db_session, owner, tenant)

    # Tạo membership + insert 1 voucher status='used'
    user_a = await _create_user(db_session, "user_reject_a@test.com")
    mem_a = await _create_membership(db_session, tenant.id, user_a.id)

    await _insert_voucher(
        db_session,
        tenant_id=tenant.id,
        campaign_id=campaign.id,
        membership_id=mem_a.id,
        code="USED0001",
        status="used",
    )

    svc = CampaignApprovalService(db_session)
    with pytest.raises(UsedVouchersBlockRejectError) as exc_info:
        await svc.reject(
            campaign_id=campaign.id,
            user_id=owner.id,
            reason="vi phạm",
            acknowledge_used_vouchers=False,
        )

    assert exc_info.value.used_count == 1


@pytest.mark.asyncio
async def test_reject_with_ack_cancels_issued_keeps_used(db_session):
    """reject(ack=True) → issued voucher cancelled, used voucher giữ nguyên."""
    owner, tenant, _, _ = await _setup(db_session)
    campaign, auth = await _make_approved_campaign(db_session, owner, tenant)

    # Member A → voucher issued (không dùng)
    user_a = await _create_user(db_session, "rej_a@test.com")
    mem_a = await _create_membership(db_session, tenant.id, user_a.id)

    # Member B → voucher used
    user_b = await _create_user(db_session, "rej_b@test.com")
    mem_b = await _create_membership(db_session, tenant.id, user_b.id)

    voucher_a = await _insert_voucher(
        db_session,
        tenant_id=tenant.id,
        campaign_id=campaign.id,
        membership_id=mem_a.id,
        code="ISSUED01",
        status="issued",
    )
    voucher_b = await _insert_voucher(
        db_session,
        tenant_id=tenant.id,
        campaign_id=campaign.id,
        membership_id=mem_b.id,
        code="USED0002",
        status="used",
    )

    svc = CampaignApprovalService(db_session)
    result_campaign, cancelled_count, used_count = await svc.reject(
        campaign_id=campaign.id,
        user_id=owner.id,
        reason="vi phạm QC",
        acknowledge_used_vouchers=True,
    )
    await db_session.flush()

    assert result_campaign.approval_status == "rejected"
    assert cancelled_count == 1
    assert used_count == 1

    # Refresh để xem trạng thái voucher
    await db_session.refresh(voucher_a)
    await db_session.refresh(voucher_b)
    assert voucher_a.status == "cancelled"
    assert voucher_b.status == "used"


# ---------------------------------------------------------------------------
# revoke authorization — C4 guard
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_revoke_blocked_after_ops_started(db_session):
    """ops_filing_started_at != None → revoke → RevokeBlockedOpsStartedError."""
    owner, tenant, campaign, auth = await _setup(db_session)

    # Đánh dấu ops started
    approval_svc = CampaignApprovalService(db_session)
    await approval_svc.mark_ops_started(campaign_id=campaign.id, user_id=owner.id)
    await db_session.flush()

    revoke_svc = TenantAuthorizationService(db_session)
    with pytest.raises(RevokeBlockedOpsStartedError):
        await revoke_svc.revoke(
            tenant_id=tenant.id,
            auth_id=auth.id,
            user_id=owner.id,
            reason="muốn huỷ",
        )


@pytest.mark.asyncio
async def test_revoke_ok_before_ops_started(db_session):
    """ops chưa started → revoke thành công, auth.revoked_at không None."""
    owner, tenant, campaign, auth = await _setup(db_session)

    revoke_svc = TenantAuthorizationService(db_session)
    result = await revoke_svc.revoke(
        tenant_id=tenant.id,
        auth_id=auth.id,
        user_id=owner.id,
        reason="đổi ý",
    )
    await db_session.flush()

    assert result.revoked_at is not None
