"""Integration tests cho QT2 — partner đăng ký kèm giấy phép + ToS."""

import pytest
from httpx import AsyncClient

from app.models.partner import PartnerStatus

pytestmark = pytest.mark.asyncio

_VALID_BODY = {
    "name": "Cafe Test License",
    "business_license_url": "/api/uploads/licenses/1/abc.jpg",
    "accept_terms": True,
    "terms_version": "v1.0",
    "category": "cafe",
}


async def test_register_partner_persists_license_and_terms(
    client: AsyncClient, user_token: str, db_session
) -> None:
    r = await client.post(
        "/partner/register",
        headers={"Authorization": f"Bearer {user_token}"},
        json=_VALID_BODY,
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["business_license_url"] == "/api/uploads/licenses/1/abc.jpg"
    assert data["terms_version"] == "v1.0"
    assert data["terms_accepted_at"] is not None


async def test_register_partner_rejects_unaccepted_terms(
    client: AsyncClient, user_token: str
) -> None:
    body = {**_VALID_BODY, "accept_terms": False}
    r = await client.post(
        "/partner/register",
        headers={"Authorization": f"Bearer {user_token}"},
        json=body,
    )
    assert r.status_code == 422


async def test_register_partner_rejects_stale_terms_version(
    client: AsyncClient, user_token: str
) -> None:
    body = {**_VALID_BODY, "terms_version": "v0.5"}
    r = await client.post(
        "/partner/register",
        headers={"Authorization": f"Bearer {user_token}"},
        json=body,
    )
    assert r.status_code == 422


async def test_admin_approve_partner_persists_reason(
    client: AsyncClient,
    admin_token: str,
    partner_factory,
    db_session,
) -> None:
    partner = await partner_factory(db_session, status=PartnerStatus.PENDING)
    r = await client.post(
        f"/admin/partners/{partner.id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"approve": True, "reason": "docs ok"},
    )
    assert r.status_code == 200, r.text
    await db_session.refresh(partner)
    assert partner.last_status_reason == "docs ok"
    assert partner.last_status_changed_by is not None
    assert partner.last_status_changed_at is not None
