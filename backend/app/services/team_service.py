from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.core.security import hash_password
from app.models import AdminUser, Enquiry
from app.services.assignment_service import OPEN_STATUSES


def list_members(db: Session) -> list[dict]:
    totals = dict(db.execute(select(Enquiry.assigned_to_id, func.count()).where(Enquiry.assigned_to_id.is_not(None)).group_by(Enquiry.assigned_to_id)).all())
    opened = dict(db.execute(
        select(Enquiry.assigned_to_id, func.count())
        .where(Enquiry.assigned_to_id.is_not(None), Enquiry.status.in_(OPEN_STATUSES))
        .group_by(Enquiry.assigned_to_id)
    ).all())
    members = db.scalars(select(AdminUser).order_by(AdminUser.id)).all()
    return [
        {
            "id": m.id, "username": m.username, "email": m.email, "role": m.role, "is_active": m.is_active,
            "open_enquiries": opened.get(m.id, 0), "total_assigned": totals.get(m.id, 0), "created_at": m.created_at,
        }
        for m in members
    ]


def create_member(db: Session, username: str, email: str, password: str, role: str) -> AdminUser:
    if db.scalar(select(AdminUser.id).where(AdminUser.username == username)):
        raise ConflictError("That username is already taken.")
    if db.scalar(select(AdminUser.id).where(AdminUser.email == email.lower())):
        raise ConflictError("That email address is already used by another team member.")
    member = AdminUser(username=username, email=email.lower(), password_hash=hash_password(password), role=role, is_active=True)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def update_member(db: Session, member_id: int, acting: AdminUser, is_active: bool | None, role: str | None) -> AdminUser:
    member = db.get(AdminUser, member_id)
    if member is None:
        raise NotFoundError(f"Team member {member_id} not found")
    if member.id == acting.id and (is_active is False or (role is not None and role != "admin")):
        raise AppError("You cannot deactivate or demote your own account.")
    if is_active is not None:
        member.is_active = is_active
    if role is not None:
        member.role = role
    # never leave the system without an active administrator
    admins_left = db.scalar(select(func.count()).select_from(AdminUser).where(AdminUser.role == "admin", AdminUser.is_active.is_(True)))
    if not admins_left:
        db.rollback()
        raise ConflictError("At least one active administrator is required.")
    db.commit()
    db.refresh(member)
    return member
