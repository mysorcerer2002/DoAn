import pytest

from app.core.security import create_access_token
from app.models.partner import Partner, PartnerStatus
from app.models.partner_staff import PartnerStaff, PartnerStaffRole
from app.models.user import User
from app.models.verification_code import VerificationCodePurpose
from app.services.verification_code_service import VerificationCodeService


async def _make_active_partner_with_owner(db_session):
    """Tạo owner + partner active + staff link, trả (partner, owner, token)."""
    owner = User(
        email="owner-claim@example.com",
        password_hash="$2b$12$dummy",
        is_active=True,
        is_shadow=False,
        system_role="regular",
    )
    db_session.add(owner)
    await db_session.flush()

    partner = Partner(
        name="ClaimShop",
        slug="claim-shop",
        owner_user_id=owner.id,
        status=PartnerStatus.ACTIVE,
        settings={},
    )
    db_session.add(partner)
    await db_session.flush()

    db_session.add(
        PartnerStaff(
            partner_id=partner.id,
            user_id=owner.id,
            role=PartnerStaffRole.OWNER,
        )
    )
    await db_session.flush()
    token = create_access_token(user_id=owner.id)
    return partner, owner, token


@pytest.mark.asyncio
async def test_request_claim_for_shadow_user_returns_202(client, db_session):
    shadow = User(
        email="shadow@example.com",
        password_hash=None,
        is_active=True,
        is_shadow=True,
        system_role="regular",
    )
    db_session.add(shadow)
    await db_session.flush()

    response = await client.post(
        "/auth/request-claim",
        json={"email": "shadow@example.com"},
    )
    assert response.status_code == 202


@pytest.mark.asyncio
async def test_request_claim_for_nonexistent_email_returns_202(client, db_session):
    """Không leak thông tin user tồn tại hay không."""
    response = await client.post(
        "/auth/request-claim",
        json={"email": "noone@example.com"},
    )
    assert response.status_code == 202


@pytest.mark.asyncio
async def test_claim_shadow_with_correct_code_succeeds(client, db_session):
    shadow = User(
        email="claim-ok@example.com",
        password_hash=None,
        is_active=True,
        is_shadow=True,
        system_role="regular",
    )
    db_session.add(shadow)
    await db_session.flush()

    vcs = VerificationCodeService(db_session)
    code = await vcs.create_code(
        user_id=shadow.id, purpose=VerificationCodePurpose.CLAIM_SHADOW
    )
    await db_session.flush()

    response = await client.post(
        "/auth/claim-shadow",
        json={
            "email": "claim-ok@example.com",
            "code": code,
            "password": "newpass12345",
            "full_name": "Claimed User",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_claim_shadow_with_wrong_code_returns_401(client, db_session):
    shadow = User(
        email="claim-bad@example.com",
        password_hash=None,
        is_active=True,
        is_shadow=True,
        system_role="regular",
    )
    db_session.add(shadow)
    await db_session.flush()

    vcs = VerificationCodeService(db_session)
    await vcs.create_code(
        user_id=shadow.id, purpose=VerificationCodePurpose.CLAIM_SHADOW
    )
    await db_session.flush()

    response = await client.post(
        "/auth/claim-shadow",
        json={
            "email": "claim-bad@example.com",
            "code": "000000",
            "password": "newpass12345",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_claim_shadow_user_can_login_after_claim(client, db_session):
    shadow = User(
        email="claim-login@example.com",
        password_hash=None,
        is_active=True,
        is_shadow=True,
        system_role="regular",
    )
    db_session.add(shadow)
    await db_session.flush()

    vcs = VerificationCodeService(db_session)
    code = await vcs.create_code(
        user_id=shadow.id, purpose=VerificationCodePurpose.CLAIM_SHADOW
    )
    await db_session.flush()

    # Claim
    claim_resp = await client.post(
        "/auth/claim-shadow",
        json={
            "email": "claim-login@example.com",
            "code": code,
            "password": "mypassword123",
        },
    )
    assert claim_resp.status_code == 200

    # Login với password mới
    login_resp = await client.post(
        "/auth/login",
        json={"email": "claim-login@example.com", "password": "mypassword123"},
    )
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_claim_shadow_for_non_shadow_user_returns_401(client, db_session):
    regular = User(
        email="regular@example.com",
        password_hash="$2b$12$dummy",
        is_active=True,
        is_shadow=False,
        system_role="regular",
    )
    db_session.add(regular)
    await db_session.flush()

    response = await client.post(
        "/auth/claim-shadow",
        json={
            "email": "regular@example.com",
            "code": "123456",
            "password": "newpass12345",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_e2e_owner_adds_staff_then_staff_claims_and_logs_in(client, db_session):
    """E2E: Owner thêm staff → staff claim → staff login → staff truy cập partner."""
    partner, _owner, owner_token = await _make_active_partner_with_owner(db_session)

    # Owner thêm staff mới
    add_resp = await client.post(
        "/partner/staff",
        json={"email": "newstaff@example.com", "full_name": "Staff", "role": "staff"},
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Partner-Id": str(partner.id),
        },
    )
    assert add_resp.status_code == 201
    code = add_resp.json()["verification_code"]
    assert code is not None
    assert len(code) == 6

    # Staff claim account
    claim_resp = await client.post(
        "/auth/claim-shadow",
        json={
            "email": "newstaff@example.com",
            "code": code,
            "password": "staffpass123",
            "full_name": "Staff Updated",
        },
    )
    assert claim_resp.status_code == 200
    staff_token = claim_resp.json()["access_token"]

    # Staff login bằng password mới
    login_resp = await client.post(
        "/auth/login",
        json={"email": "newstaff@example.com", "password": "staffpass123"},
    )
    assert login_resp.status_code == 200

    # Staff truy cập tenant info (GET /partners/me)
    me_resp = await client.get(
        "/partners/me",
        headers={
            "Authorization": f"Bearer {staff_token}",
            "X-Partner-Id": str(partner.id),
        },
    )
    assert me_resp.status_code == 200
