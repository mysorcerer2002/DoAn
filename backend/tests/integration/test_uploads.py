"""Integration tests cho upload endpoints."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_upload_license_requires_auth(client: AsyncClient) -> None:
    fake_image = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    r = await client.post(
        "/partner/uploads/license",
        files={"file": ("license.png", fake_image, "image/png")},
    )
    assert r.status_code == 401


async def test_upload_license_returns_url(client: AsyncClient, user_token: str) -> None:
    fake_image = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    r = await client.post(
        "/partner/uploads/license",
        headers={"Authorization": f"Bearer {user_token}"},
        files={"file": ("license.png", fake_image, "image/png")},
    )
    assert r.status_code == 200, r.text
    assert r.json()["url"].startswith("/api/uploads/licenses/")
