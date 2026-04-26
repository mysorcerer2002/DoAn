import asyncio

import pytest

from app.core.exceptions import EmailDeliveryError
from app.services.email_service import EmailService


@pytest.mark.asyncio
async def test_send_email_timeout_raises(monkeypatch):
    async def fake_send(*args, **kwargs):
        await asyncio.sleep(60)

    monkeypatch.setattr("aiosmtplib.send", fake_send)
    service = EmailService(timeout=1)
    with pytest.raises(EmailDeliveryError, match="timeout"):
        await service.send_email(
            to="x@example.com",
            subject="test",
            body="hi",
        )


@pytest.mark.asyncio
async def test_send_email_smtp_error_raises(monkeypatch):
    async def fake_send(*args, **kwargs):
        raise ConnectionError("Connection refused")

    monkeypatch.setattr("aiosmtplib.send", fake_send)
    service = EmailService(timeout=10)
    with pytest.raises(EmailDeliveryError):
        await service.send_email(to="x@example.com", subject="s", body="b")
