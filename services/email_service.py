"""Email delivery service — Resend API."""

import logging
import httpx
from config import get_settings

logger = logging.getLogger(__name__)


async def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send an email via Resend API.

    Returns True on success, False on failure.
    """
    settings = get_settings()

    logger.info(f"📧 EMAIL → {to_email} | Subject: {subject}")

    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set — email not sent (demo mode)")
        return True  # graceful in demo

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": f"{settings.RESEND_FROM_NAME} <{settings.RESEND_FROM_EMAIL}>",
                    "to": [to_email],
                    "subject": subject,
                    "text": body,
                },
            )

        logger.info(f"Resend status={resp.status_code}  body={resp.text}")

        if resp.status_code in (200, 201):
            logger.info(f"✅ Email delivered to {to_email}")
            return True

        logger.error(f"❌ Resend failed {resp.status_code}: {resp.text}")
        return False

    except Exception as exc:
        logger.error(f"❌ Resend exception: {exc}")
        return False
