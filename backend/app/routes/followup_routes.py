from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_admin
from app.database.connection import get_db
from app.schemas.followup import FollowUpItem, FollowUpSummary, FollowUpUpdate
from app.schemas.response import ApiResponse, PageMeta, Paginated
from app.services import enquiry_service, reminder_service

router = APIRouter(prefix="/api/followups", tags=["Follow-up reminders"], dependencies=[Depends(get_current_admin)])


@router.get("/summary", response_model=ApiResponse[FollowUpSummary])
def followup_summary(db: Session = Depends(get_db)):
    """Counts for badges: pending, overdue, due today, done."""
    return ApiResponse(data=reminder_service.summary(db))


@router.get("", response_model=Paginated[FollowUpItem])
def list_followups(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Literal["Pending", "Done", "Dismissed"] | None = "Pending",
    overdue: bool = Query(False, description="Only pending follow-ups that are past their suggested date"),
    assignee_id: int | None = None,
    unassigned: bool = False,
    db: Session = Depends(get_db),
):
    """Reminders across all enquiries, most urgent first."""
    items, total = reminder_service.list_followups(db, page, page_size, status, overdue, assignee_id, unassigned)
    meta = PageMeta(page=page, page_size=page_size, total=total, total_pages=enquiry_service.total_pages(total, page_size))
    return Paginated(data=items, meta=meta)


@router.put("/{followup_id}", response_model=ApiResponse[FollowUpSummary])
def update_followup(followup_id: int, payload: FollowUpUpdate, db: Session = Depends(get_db)):
    """Mark a follow-up Done / Dismissed (or put it back to Pending). Returns the refreshed counts."""
    reminder_service.update_status(db, followup_id, payload.status)
    return ApiResponse(data=reminder_service.summary(db))
