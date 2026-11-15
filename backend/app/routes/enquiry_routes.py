from datetime import datetime
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.core.security import get_current_admin
from app.database.connection import get_db
from app.schemas.communication import CommunicationOut, SendEmailRequest, WhatsAppOut, WhatsAppRequest
from app.schemas.enquiry import (
    EnquiryCreate, EnquiryDetail, EnquiryOut, EnquiryStatus, EnquiryStatusUpdate, ResponseOut, ResponseUpdate,
)
from app.schemas.response import ApiResponse, PageMeta, Paginated
from app.schemas.team import AssigneeUpdate
from app.services import assignment_service, communication_service, enquiry_service, workflow_service

router = APIRouter(prefix="/api/enquiries", tags=["Enquiries"])
admin_only = [Depends(get_current_admin)]

Category = Literal[
    "Website Development", "Mobile Application Development", "AI Software Development", "Digital Marketing",
    "E-commerce Development", "Custom Software Development", "Other Services",
]

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class Filters:
    """Shared query parameters for the list and export endpoints."""

    def __init__(
        self,
        search: str | None = Query(None, max_length=100, description="Name, email, phone, message or AI summary"),
        status: EnquiryStatus | None = None,
        priority: Literal["Low", "Medium", "High"] | None = None,
        category: Category | None = None,
        temperature: Literal["Hot", "Warm", "Cold"] | None = None,
        ai_status: Literal["pending", "processing", "completed", "failed"] | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        assignee_id: int | None = Query(None, description="Only enquiries assigned to this team member"),
        unassigned: bool = Query(False, description="Only enquiries with no assignee"),
    ):
        self.values = dict(
            search=search, status=status, priority=priority, category=category, temperature=temperature,
            ai_status=ai_status, date_from=date_from, date_to=date_to, assignee_id=assignee_id, unassigned=unassigned,
        )


@router.post(
    "", response_model=ApiResponse[EnquiryOut], status_code=201,
    dependencies=[Depends(rate_limit("enquiry", "rate_limit_enquiries_per_minute"))],
)
def submit_enquiry(payload: EnquiryCreate, background: BackgroundTasks, db: Session = Depends(get_db)):
    """PUBLIC. Saves the original enquiry, auto-assigns it to a team member, then runs the AI workflow in the background."""
    enquiry = enquiry_service.create_enquiry(db, payload)
    background.add_task(workflow_service.process_enquiry, enquiry.id)
    return ApiResponse(data=enquiry)


@router.get("", response_model=Paginated[EnquiryOut], dependencies=admin_only)
def list_enquiries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    filters: Filters = Depends(),
    db: Session = Depends(get_db),
):
    rows, total = enquiry_service.list_enquiries(db, page, page_size, **filters.values)
    meta = PageMeta(page=page, page_size=page_size, total=total, total_pages=enquiry_service.total_pages(total, page_size))
    return Paginated(data=rows, meta=meta)


# NOTE: declared before "/{enquiry_id}" so "export" is not parsed as an id.
@router.get(
    "/export", dependencies=admin_only, response_class=Response,
    responses={200: {"content": {"text/csv": {}, XLSX_MIME: {}}, "description": "CSV or Excel file"}},
)
def export_enquiries(
    format: Literal["csv", "xlsx"] = Query("csv", description="csv or xlsx (Excel)"),
    filters: Filters = Depends(),
    db: Session = Depends(get_db),
):
    if format == "xlsx":
        return Response(
            content=enquiry_service.export_xlsx(db, **filters.values), media_type=XLSX_MIME,
            headers={"Content-Disposition": 'attachment; filename="enquiries.xlsx"'},
        )
    return Response(
        content=enquiry_service.export_csv(db, **filters.values), media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="enquiries.csv"'},
    )


@router.get("/{enquiry_id}", response_model=ApiResponse[EnquiryDetail], dependencies=admin_only)
def get_enquiry(enquiry_id: int, db: Session = Depends(get_db)):
    return ApiResponse(data=enquiry_service.get_enquiry(db, enquiry_id))


@router.put("/{enquiry_id}/status", response_model=ApiResponse[EnquiryOut], dependencies=admin_only)
def update_status(enquiry_id: int, payload: EnquiryStatusUpdate, db: Session = Depends(get_db)):
    return ApiResponse(data=enquiry_service.update_status(db, enquiry_id, payload.status))


@router.put("/{enquiry_id}/assignee", response_model=ApiResponse[EnquiryOut], dependencies=admin_only)
def set_assignee(enquiry_id: int, payload: AssigneeUpdate, db: Session = Depends(get_db)):
    """Manually (re)assign an enquiry, or unassign it with `assignee_id: null`."""
    enquiry = enquiry_service.get_enquiry(db, enquiry_id)
    return ApiResponse(data=assignment_service.assign_to(db, enquiry, payload.assignee_id))


@router.post("/{enquiry_id}/auto-assign", response_model=ApiResponse[EnquiryOut], dependencies=admin_only)
def auto_assign(enquiry_id: int, db: Session = Depends(get_db)):
    """Run the automatic assignment rules again (e.g. after adding team members)."""
    enquiry = enquiry_service.get_enquiry(db, enquiry_id)
    assignment_service.auto_assign(db, enquiry)
    return ApiResponse(data=enquiry)


@router.post("/{enquiry_id}/reanalyze", response_model=ApiResponse[EnquiryOut], status_code=202, dependencies=admin_only)
def reanalyze(enquiry_id: int, background: BackgroundTasks, db: Session = Depends(get_db)):
    """Retry AI processing (e.g. after a failure). Safe to repeat: records are updated, never duplicated."""
    enquiry = enquiry_service.ensure_can_reanalyze(db, enquiry_id)
    background.add_task(workflow_service.process_enquiry, enquiry.id)
    return ApiResponse(data=enquiry)


@router.put("/{enquiry_id}/response", response_model=ApiResponse[ResponseOut], dependencies=admin_only)
def edit_response(enquiry_id: int, payload: ResponseUpdate, db: Session = Depends(get_db)):
    return ApiResponse(data=enquiry_service.update_response(db, enquiry_id, payload.edited_response))


@router.post("/{enquiry_id}/send-email", response_model=ApiResponse[CommunicationOut], status_code=201)
def send_email(enquiry_id: int, payload: SendEmailRequest, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    """Email the reply to the customer over SMTP (the edited reply if there is one). 409 if SMTP is not configured."""
    enquiry = enquiry_service.get_enquiry(db, enquiry_id)
    return ApiResponse(data=communication_service.send_customer_email(db, enquiry, admin, payload.subject, payload.body))


@router.post("/{enquiry_id}/whatsapp", response_model=ApiResponse[WhatsAppOut], status_code=201)
def whatsapp(enquiry_id: int, payload: WhatsAppRequest, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    """Prepare a WhatsApp click-to-chat link with the reply pre-filled and log it. The admin presses send in WhatsApp."""
    enquiry = enquiry_service.get_enquiry(db, enquiry_id)
    link, comm = communication_service.prepare_whatsapp(db, enquiry, admin, payload.text)
    return ApiResponse(data=WhatsAppOut(link=link, communication=comm))
