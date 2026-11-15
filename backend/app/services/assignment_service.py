"""Automatic assignment of new enquiries to team members.

Rules, in order:
  1. Customer continuity - if this customer (same email or phone) already has an enquiry assigned to an
     ACTIVE team member, give the new one to the same person.
  2. Load balancing - otherwise pick the active member with the fewest OPEN enquiries (New / In Progress).
  3. Round-robin tie-break - among equals, the member who was assigned something least recently goes first.
Inactive members never receive new enquiries. With no active members the enquiry stays unassigned.
"""
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import AdminUser, Enquiry

OPEN_STATUSES = ("New", "In Progress")


def open_load(db: Session) -> dict[int, int]:
    rows = db.execute(
        select(Enquiry.assigned_to_id, func.count())
        .where(Enquiry.assigned_to_id.is_not(None), Enquiry.status.in_(OPEN_STATUSES))
        .group_by(Enquiry.assigned_to_id)
    ).all()
    return {uid: n for uid, n in rows}


def _last_assigned(db: Session) -> dict[int, datetime]:
    rows = db.execute(
        select(Enquiry.assigned_to_id, func.max(Enquiry.assigned_at))
        .where(Enquiry.assigned_to_id.is_not(None))
        .group_by(Enquiry.assigned_to_id)
    ).all()
    return {uid: ts for uid, ts in rows if ts}


def _set(db: Session, enquiry: Enquiry, member: AdminUser | None) -> None:
    enquiry.assigned_to_id = member.id if member else None
    enquiry.assigned_at = datetime.now(timezone.utc) if member else None
    db.commit()
    db.refresh(enquiry)


def auto_assign(db: Session, enquiry: Enquiry) -> tuple[AdminUser | None, str]:
    """Returns (member or None, human-readable reason) - the reason is written to the workflow history."""
    members = db.scalars(select(AdminUser).where(AdminUser.is_active.is_(True)).order_by(AdminUser.id)).all()
    if not members:
        return None, "No active team members, left unassigned"
    by_id = {m.id: m for m in members}

    conditions = []
    if enquiry.email:
        conditions.append(Enquiry.email == enquiry.email)
    if enquiry.phone:
        conditions.append(Enquiry.phone == enquiry.phone)
    if conditions:
        prior = db.scalars(
            select(Enquiry)
            .where(Enquiry.id != enquiry.id, Enquiry.assigned_to_id.is_not(None), or_(*conditions))
            .order_by(Enquiry.id.desc())
            .limit(1)
        ).first()
        if prior and prior.assigned_to_id in by_id:
            member = by_id[prior.assigned_to_id]
            _set(db, enquiry, member)
            return member, f"Assigned to {member.username}: returning customer (previous enquiry #{prior.id})"

    load, last = open_load(db), _last_assigned(db)
    epoch = datetime.min.replace(tzinfo=timezone.utc)

    def key(m: AdminUser):
        ts = last.get(m.id, epoch)
        return (load.get(m.id, 0), ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts, m.id)

    member = min(members, key=key)
    _set(db, enquiry, member)
    return member, f"Assigned to {member.username}: fewest open enquiries ({load.get(member.id, 0)} open)"


def assign_to(db: Session, enquiry: Enquiry, member_id: int | None) -> Enquiry:
    member = None
    if member_id is not None:
        member = db.get(AdminUser, member_id)
        if member is None:
            raise NotFoundError(f"Team member {member_id} not found")
    _set(db, enquiry, member)
    return enquiry
