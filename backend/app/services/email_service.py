import asyncio
import logging
from email.message import EmailMessage

import aiosmtplib

from app.core.config import get_settings
from app.core.exceptions import EmailDeliveryError

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, timeout: int | None = None):
        _settings = get_settings()
        self.timeout = timeout if timeout is not None else _settings.smtp_timeout
        self._settings = _settings

    async def send_email(self, to: str, subject: str, body: str) -> None:
        s = self._settings
        msg = EmailMessage()
        msg["From"] = f"{s.smtp_from_name} <{s.smtp_from_email}>"
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        try:
            await asyncio.wait_for(
                aiosmtplib.send(
                    msg,
                    hostname=s.smtp_host,
                    port=s.smtp_port,
                    username=s.smtp_user,
                    password=s.smtp_password,
                    start_tls=True,
                ),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError as e:
            logger.warning("email_service.timeout", extra={"to": to, "subject": subject})
            raise EmailDeliveryError(f"SMTP send timeout after {self.timeout}s") from e
        except Exception as e:
            logger.warning("email_service.error", extra={"to": to, "error": str(e)})
            raise EmailDeliveryError(f"SMTP send failed: {e}") from e
