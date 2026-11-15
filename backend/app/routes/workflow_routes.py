from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import get_current_admin
from app.database.connection import get_db
from app.models import WorkflowLog
from app.schemas.dashboard import WorkflowLogOut
from app.schemas.response import ApiResponse, PageMeta, Paginated
from app.services import enquiry_service

router = APIRouter(prefix="/api/workflows", tags=["Workflows"], dependencies=[Depends(get_current_admin)])


@router.get("", response_model=Paginated[WorkflowLogOut])
def list_workflow_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: Literal["started", "success", "failed", "skipped"] | None = None,
    step: str | None = Query(None, max_length=80),
    db: Session = Depends(get_db),
):
    stmt = select(WorkflowLog)
    if status:
        stmt = stmt.where(WorkflowLog.execution_status == status)
    if step:
        stmt = stmt.where(WorkflowLog.workflow_step == step)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(WorkflowLog.created_at.desc(), WorkflowLog.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    meta = PageMeta(page=page, page_size=page_size, total=total, total_pages=enquiry_service.total_pages(total, page_size))
    return Paginated(data=rows, meta=meta)


@router.get("/{enquiry_id}", response_model=ApiResponse[list[WorkflowLogOut]])
def enquiry_timeline(enquiry_id: int, db: Session = Depends(get_db)):
    """Chronological execution history for one enquiry (oldest first) — feeds the timeline UI."""
    enquiry_service.get_enquiry(db, enquiry_id)  # 404 if the enquiry doesn't exist
    rows = db.scalars(
        select(WorkflowLog).where(WorkflowLog.enquiry_id == enquiry_id).order_by(WorkflowLog.created_at, WorkflowLog.id)
    ).all()
    return ApiResponse(data=list(rows))
