"""Real SMTP sending (standard library). If SMTP is not configured nothing is sent and callers are told so."""
import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.utils.helpers import scrub_secrets

logger = logging.getLogger("leadflow.email")


class EmailNotConfigured(AppError):
    status_code = 409
    code = "email_not_configured"


class EmailSendError(AppError):
    status_code = 502
    code = "email_failed"


def is_configured() -> bool:
    return get_settings().email_enabled


def _clean_header(value: str) -> str:
    return " ".join(value.replace("\r", " ").replace("\n", " ").split())[:300]  # blocks header injection


def send_email(to: list[str], subject: str, body: str, reply_to: str | None = None) -> None:
    s = get_settings()
    if not s.email_enabled:
        raise EmailNotConfigured("Email sending is not configured on the server (set SMTP_HOST and SMTP_FROM).")
    recipients = [_clean_header(r) for r in to if r and r.strip()]
    if not recipients:
        raise EmailSendError("There is no recipient email address.")

    msg = EmailMessage()
    msg["From"] = _clean_header(s.smtp_from or "")
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = _clean_header(subject)
    if reply_to:
        msg["Reply-To"] = _clean_header(reply_to)
    msg.set_content(body)

    try:
        if s.smtp_security == "ssl":
            server: smtplib.SMTP = smtplib.SMTP_SSL(
                s.smtp_host, s.smtp_port, timeout=s.smtp_timeout_seconds, context=ssl.create_default_context()
            )
        else:
            server = smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=s.smtp_timeout_seconds)
        with server:
            if s.smtp_security == "starttls":
                server.starttls(context=ssl.create_default_context())
            if s.smtp_username:
                server.login(s.smtp_username, s.smtp_password or "")
            server.send_message(msg)
    except (smtplib.SMTPException, OSError, ValueError) as e:
        logger.warning("email send failed: %s", scrub_secrets(f"{type(e).__name__}: {e}")[:200])
        raise EmailSendError(f"The email could not be sent ({type(e).__name__}). Check the SMTP settings.") from e
