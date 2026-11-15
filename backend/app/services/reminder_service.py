"""Follow-up reminders: a cross-enquiry view of the suggested follow-up actions, with overdue tracking."""
from datetime import datetime, timezone

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import Enquiry, FollowUp


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _base() -> Select:
    return select(FollowUp, Enquiry).join(Enquiry, Enquiry.id == FollowUp.enquiry_id)


def list_followups(
    db: Session, page: int, page_size: int, status: str | None, overdue_only: bool,
    assignee_id: int | None, unassigned: bool,
) -> tuple[list[dict], int]:
    stmt = _base()
    if status:
        stmt = stmt.where(FollowUp.status == status)
    if overdue_only:
        stmt = stmt.where(FollowUp.status == "Pending", FollowUp.suggested_date < _now())
    if assignee_id is not None:
        stmt = stmt.where(Enquiry.assigned_to_id == assignee_id)
    if unassigned:
        stmt = stmt.where(Enquiry.assigned_to_id.is_(None))
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    # most urgent first: items with a date by date ascending, undated last
    rows = db.execute(
        stmt.order_by(FollowUp.suggested_date.is_(None), FollowUp.suggested_date, FollowUp.id).offset((page - 1) * page_size).limit(page_size)
    ).all()
    now = _now()

    def due(fu: FollowUp) -> datetime | None:
        d = fu.suggested_date
        return d.replace(tzinfo=timezone.utc) if d is not None and d.tzinfo is None else d

    items = [
        {
            "id": fu.id, "enquiry_id": e.id, "customer_name": e.customer_name, "enquiry_priority": e.priority,
            "lead_temperature": e.lead_temperature, "assigned_to_name": e.assigned_to_name,
            "suggested_action": fu.suggested_action, "suggested_date": fu.suggested_date, "status": fu.status,
            "is_overdue": fu.status == "Pending" and due(fu) is not None and due(fu) < now, "created_at": fu.created_at,
        }
        for fu, e in rows
    ]
    return items, total


def summary(db: Session) -> dict:
    now = _now()
    end_of_today = now.replace(hour=23, minute=59, second=59, microsecond=0)

    def count(*conds) -> int:
        return db.scalar(select(func.count()).select_from(FollowUp).where(*conds)) or 0

    return {
        "pending": count(FollowUp.status == "Pending"),
        "overdue": count(FollowUp.status == "Pending", FollowUp.suggested_date < now),
        "due_today": count(FollowUp.status == "Pending", FollowUp.suggested_date >= now, FollowUp.suggested_date <= end_of_today),
        "done": count(FollowUp.status == "Done"),
    }


def update_status(db: Session, followup_id: int, status: str) -> FollowUp:
    fu = db.get(FollowUp, followup_id)
    if fu is None:
        raise NotFoundError(f"Follow-up {followup_id} not found")
    fu.status = status
    db.commit()
    db.refresh(fu)
    return fu



