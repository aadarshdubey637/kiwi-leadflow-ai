"""Internal email alerts to the team. Never raises: a failed alert must not break enquiry processing."""
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Communication, Enquiry
from app.services import communication_service, email_service
from app.utils.helpers import scrub_secrets

logger = logging.getLogger("leadflow.notify")


def _recipients(enquiry: Enquiry) -> list[str]:
    s = get_settings()
    out: list[str] = []
    if enquiry.assignee and enquiry.assignee.is_active and enquiry.assignee.email:
        out.append(enquiry.assignee.email)  # the person responsible always hears about it
    urgent = enquiry.priority == "High" or enquiry.lead_temperature == "Hot" or enquiry.needs_manual_review
    if s.notify_all_enquiries or urgent:
        out.extend(s.notify_emails)
    seen: set[str] = set()
    return [e for e in out if not (e.lower() in seen or seen.add(e.lower()))]


def build_message(enquiry: Enquiry) -> tuple[str, str]:
    s = get_settings()
    a = enquiry.analysis
    tag = "Hot lead" if enquiry.lead_temperature == "Hot" else "New enquiry"
    subject = f"[LeadFlow] {tag}: {enquiry.customer_name} ({a.service_category if a else 'unclassified'}) #{enquiry.id}"
    lines = [
        f"{tag} #{enquiry.id} from {enquiry.customer_name}",
        "",
        f"Service:   {a.service_category if a else 'not analysed'}",
        f"Priority:  {enquiry.priority or '-'}  ({enquiry.priority_reason or 'n/a'})",
        f"Lead:      {enquiry.lead_temperature or '-'}"
        + (f" ({enquiry.lead_score_total}/100)" if enquiry.lead_score_total is not None else ""),
        f"Assigned:  {enquiry.assigned_to_name or 'unassigned'}",
        f"Contact:   {enquiry.email or '-'}  {enquiry.phone or ''}".rstrip(),
    ]
    if a and a.summary:
        lines += ["", "Summary:", a.summary]
    if enquiry.needs_manual_review:
        lines += ["", "! The AI flagged this enquiry for manual review."]
    if enquiry.duplicate_of_id:
        lines += ["", f"! Possible duplicate of enquiry #{enquiry.duplicate_of_id} ({enquiry.duplicate_reason})."]
    lines += ["", f"Open it: {s.frontend_url.rstrip('/')}/admin/enquiries/{enquiry.id}"]
    return subject, "\n".join(lines)


def notify_new_enquiry(db: Session, enquiry_id: int) -> tuple[str, str]:
    """Returns (status, message) where status is success | skipped | failed, for the workflow log."""
    try:
        if not email_service.is_configured():
            return "skipped", "Email is not configured (set SMTP_HOST and SMTP_FROM to enable alerts)"
        enquiry = db.get(Enquiry, enquiry_id)
        if enquiry is None:
            return "skipped", "Enquiry not found"
        already = db.scalar(
            select(Communication.id).where(
                Communication.enquiry_id == enquiry_id,
                Communication.kind == "team_notification",
                Communication.status == "sent",
            )
        )
        if already:
            return "skipped", "Team was already notified (not sending again on re-analysis)"
        to = _recipients(enquiry)
        if not to:
            return "skipped", "No one to notify (enquiry unassigned and not urgent)"
        subject, body = build_message(enquiry)
        try:
            email_service.send_email(to, subject, body)
        except email_service.EmailSendError as e:
            communication_service.record(db, enquiry_id, "email", "team_notification", ", ".join(to), subject, body, "failed", e.message)
            return "failed", e.message
        communication_service.record(db, enquiry_id, "email", "team_notification", ", ".join(to), subject, body, "sent")
        return "success", f"Alert emailed to {', '.join(to)}"
    except Exception as e:  # noqa: BLE001 - alerts must never break processing
        db.rollback()
        logger.warning("notification error: %s", scrub_secrets(str(e))[:200])
        return "failed", f"Notification error ({type(e).__name__})"
