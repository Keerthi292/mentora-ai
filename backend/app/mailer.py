"""Sending emails over SMTP (Python's standard library, no extra package).

Without SMTP_HOST in backend/.env nothing is sent: the email is printed in the
backend's terminal instead, so "forgot password" still works on your own computer.
"""

import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


def email_configured() -> bool:
    return bool(settings.SMTP_HOST.strip())


def send_email(to: str, subject: str, text: str) -> None:
    if not email_configured():
        logger.info("✉ Email to %s (no SMTP_HOST, so printed here)\n%s\n%s", to, subject, text)
        return

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM or settings.SMTP_USER
    message["To"] = to
    message["Subject"] = subject
    message.set_content(text)

    password = settings.SMTP_PASSWORD.get_secret_value() if settings.SMTP_PASSWORD else ""
    try:
        # Port 465 is TLS from the start; other ports (587) upgrade with STARTTLS
        if settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20)
            server.starttls()
        with server:
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, password)
            server.send_message(message)
    except (OSError, smtplib.SMTPException):
        # Runs in the background after the response, so the user can't be told; log it
        logger.exception("Could not send the email to %s", to)
