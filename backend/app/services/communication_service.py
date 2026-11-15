"""Customer-facing communication: email replies and WhatsApp click-to-chat, with an audit trail."""
import re
from urllib.parse import quote

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ConflictError
from app.models import AdminUser, Communication, Enquiry
from app.services import email_service


def record(
    db: Session, enquiry_id: int, channel: str, kind: str, recipient: str, subject: str | None, body: str | None,
    status: str, error: str | None = None, sent_by: AdminUser | None = None,
) -> Communication:
    comm = Communication(
        enquiry_id=enquiry_id, channel=channel, kind=kind, recipient=recipient[:400], subject=subject, body=body,
        status=status, error=(error or "")[:300] or None, sent_by_id=sent_by.id if sent_by else None,
    )
    db.add(comm)
    db.commit()
    db.refresh(comm)
    return comm


def _reply_text(enquiry: Enquiry) -> str | None:
    return enquiry.response.final_response if enquiry.response else None


def send_customer_email(db: Session, enquiry: Enquiry, admin: AdminUser, subject: str | None, body: str | None) -> Communication:
    if not enquiry.email:
        raise ConflictError("This enquiry has no email address.")
    if not email_service.is_configured():
        raise email_service.EmailNotConfigured("Email sending is not configured on the server (set SMTP_HOST and SMTP_FROM).")
    text = (body or _reply_text(enquiry) or "").strip()
    if not text:
        raise ConflictError("There is no reply text to send yet. Wait for the AI draft or write one first.")
    subj = (subject or f"Re: your enquiry with {get_settings().company_name}").strip()
    try:
        email_service.send_email([enquiry.email], subj, text)
    except email_service.EmailSendError as e:
        record(db, enquiry.id, "email", "customer_reply", enquiry.email, subj, text, "failed", e.message, admin)
        raise
    return record(db, enquiry.id, "email", "customer_reply", enquiry.email, subj, text, "sent", None, admin)


def whatsapp_number(phone: str) -> str:
    """wa.me wants digits only, with country code. Numbers saved as 10 digits get the default country code."""
    raw = phone.strip()
    digits = re.sub(r"\D", "", raw)
    if not raw.startswith("+") and len(digits) == 10:
        digits = get_settings().default_country_code + digits
    if not 8 <= len(digits) <= 15:
        raise ConflictError("This phone number cannot be used for WhatsApp.")
    return digits


def prepare_whatsapp(db: Session, enquiry: Enquiry, admin: AdminUser, text: str | None) -> tuple[str, Communication]:
    if not enquiry.phone:
        raise ConflictError("This enquiry has no phone number.")
    message = (text or _reply_text(enquiry) or "").strip()
    if not message:
        raise ConflictError("There is no reply text to send yet. Wait for the AI draft or write one first.")
    number = whatsapp_number(enquiry.phone)
    link = f"https://wa.me/{number}?text={quote(message, safe='')}"
    # 'opened': we hand the admin a ready-to-send chat. WhatsApp gives us no way to know whether they pressed send.
    comm = record(db, enquiry.id, "whatsapp", "customer_reply", f"+{number}", None, message, "opened", None, admin)
    return link, comm
