import csv
import io
import math
from datetime import datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.models import AIAnalysis, AIResponse, Enquiry, LeadScore
from app.schemas.enquiry import EnquiryCreate
from app.services import assignment_service
from app.services.workflow_service import is_processing, log_step


def create_enquiry(db: Session, data: EnquiryCreate) -> Enquiry:
    """Persist the original enquiry first — it must survive any later AI failure."""
    enquiry = Enquiry(
        customer_name=data.customer_name,
        phone=data.phone,
        email=data.email.lower() if data.email else None,
        message=data.message,
        source=data.source,
    )
    db.add(enquiry)
    db.commit()
    db.refresh(enquiry)
    log_step(db, enquiry.id, "enquiry_received", "success", f"Received via {enquiry.source}")
    log_step(db, enquiry.id, "original_data_saved", "success", "Original enquiry stored")
    # Automatic assignment happens immediately (before the slower AI step) so ownership is never delayed by the LLM.
    try:
        member, reason = assignment_service.auto_assign(db, enquiry)
        log_step(db, enquiry.id, "team_assignment", "success" if member else "skipped", reason)
    except Exception as e:  # noqa: BLE001 - assignment problems must never lose the enquiry
        db.rollback()
        log_step(db, enquiry.id, "team_assignment", "failed", f"Auto-assignment failed ({type(e).__name__})")
    return enquiry


def get_enquiry(db: Session, enquiry_id: int) -> Enquiry:
    enquiry = db.get(Enquiry, enquiry_id)
    if enquiry is None:
        raise NotFoundError(f"Enquiry {enquiry_id} not found")
    return enquiry


def _escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _filtered(
    search: str | None, status: str | None, priority: str | None, category: str | None,
    temperature: str | None, ai_status: str | None, date_from: datetime | None, date_to: datetime | None,
    assignee_id: int | None = None, unassigned: bool = False,
) -> Select:
    stmt = (
        select(Enquiry)
        .outerjoin(AIAnalysis, AIAnalysis.enquiry_id == Enquiry.id)
        .outerjoin(LeadScore, LeadScore.enquiry_id == Enquiry.id)
        .options(selectinload(Enquiry.analysis), selectinload(Enquiry.lead_score))
    )
    if status:
        stmt = stmt.where(Enquiry.status == status)
    if priority:
        stmt = stmt.where(Enquiry.priority == priority)
    if category:
        stmt = stmt.where(AIAnalysis.service_category == category)
    if temperature:
        stmt = stmt.where(LeadScore.lead_temperature == temperature)
    if ai_status:
        stmt = stmt.where(Enquiry.ai_status == ai_status)
    if assignee_id is not None:
        stmt = stmt.where(Enquiry.assigned_to_id == assignee_id)
    if unassigned:
        stmt = stmt.where(Enquiry.assigned_to_id.is_(None))
    if date_from:
        stmt = stmt.where(Enquiry.created_at >= date_from)
    if date_to:
        stmt = stmt.where(Enquiry.created_at <= date_to)
    if search and search.strip():
        like = f"%{_escape_like(search.strip())}%"
        stmt = stmt.where(or_(
            Enquiry.customer_name.ilike(like, escape="\\"),
            Enquiry.email.ilike(like, escape="\\"),
            Enquiry.phone.ilike(like, escape="\\"),
            Enquiry.message.ilike(like, escape="\\"),
            AIAnalysis.summary.ilike(like, escape="\\"),
        ))
    return stmt


def list_enquiries(db: Session, page: int = 1, page_size: int = 20, **filters) -> tuple[list[Enquiry], int]:
    stmt = _filtered(**_fill(filters))
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Enquiry.created_at.desc(), Enquiry.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return list(rows), total


def _fill(filters: dict) -> dict:
    keys = ("search", "status", "priority", "category", "temperature", "ai_status", "date_from", "date_to", "assignee_id", "unassigned")
    return {k: filters.get(k) for k in keys}


def total_pages(total: int, page_size: int) -> int:
    return max(1, math.ceil(total / page_size))


def update_status(db: Session, enquiry_id: int, status: str) -> Enquiry:
    enquiry = get_enquiry(db, enquiry_id)
    enquiry.status = status
    db.commit()
    db.refresh(enquiry)
    return enquiry


def update_response(db: Session, enquiry_id: int, edited: str) -> AIResponse:
    enquiry = get_enquiry(db, enquiry_id)
    if enquiry.response is None:
        raise ConflictError("No AI response has been generated for this enquiry yet")
    enquiry.response.edited_response = edited  # generated_response stays untouched
    db.commit()
    db.refresh(enquiry.response)
    return enquiry.response


def ensure_can_reanalyze(db: Session, enquiry_id: int) -> Enquiry:
    enquiry = get_enquiry(db, enquiry_id)
    if is_processing(enquiry):
        raise ConflictError("This enquiry is already being processed")
    return enquiry


# ---------- export (CSV / Excel) ----------

EXPORT_COLUMNS = [
    "id", "customer_name", "email", "phone", "status", "priority", "service_category", "budget", "currency",
    "customer_location", "urgency", "lead_score", "lead_temperature", "sentiment", "summary", "assigned_to",
    "ai_status", "needs_manual_review", "duplicate_of_id", "created_at",
]
CSV_COLUMNS = EXPORT_COLUMNS  # backwards-compatible name


# characters that make Excel/Sheets treat a cell as a formula (chr(9)=TAB, chr(13)=CR)
_FORMULA_PREFIXES = ('=', '+', '-', '@', chr(9), chr(13))


def _safe_cell(value) -> str:
    """Neutralise spreadsheet formula injection: a customer-supplied '=cmd()' must not execute in Excel."""
    text = '' if value is None else str(value)
    return "'" + text if text[:1] in _FORMULA_PREFIXES else text


def _export_rows(db: Session, **filters) -> list[list]:
    """Raw (unescaped) values; each writer applies the escaping its format needs."""
    rows = db.scalars(_filtered(**_fill(filters)).order_by(Enquiry.created_at.desc(), Enquiry.id.desc())).all()
    out = []
    for e in rows:
        a = e.analysis
        out.append([
            e.id, e.customer_name, e.email, e.phone, e.status, e.priority,
            a.service_category if a else None, float(a.budget) if a and a.budget is not None else None, a.currency if a else None,
            a.customer_location if a else None, a.urgency if a else None,
            e.lead_score_total, e.lead_temperature, a.sentiment if a else None, a.summary if a else None, e.assigned_to_name,
            e.ai_status, e.needs_manual_review, e.duplicate_of_id, e.created_at.isoformat(),
        ])
    return out


def export_csv(db: Session, **filters) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(EXPORT_COLUMNS)
    for row in _export_rows(db, **filters):
        # phone is validated as digits with an optional leading '+', so it is safe to write unescaped
        writer.writerow([(v or "") if col == "phone" else _safe_cell(v) for col, v in zip(EXPORT_COLUMNS, row)])
    return buf.getvalue()


def export_xlsx(db: Session, **filters) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = Workbook()
    ws = wb.active
    ws.title = "Enquiries"
    ws.append([c.replace("_", " ").title().replace("Ai ", "AI ").replace(" Id", " ID") for c in EXPORT_COLUMNS])
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="175A55")
        cell.alignment = Alignment(vertical="center")
    for row in _export_rows(db, **filters):
        ws.append(row)
        for cell in ws[ws.max_row]:
            # openpyxl turns any string starting with '=' into a FORMULA; force text so customer input can never execute
            if isinstance(cell.value, str):
                cell.data_type = "s"
    widths = {"customer_name": 22, "email": 28, "summary": 50, "service_category": 30, "created_at": 26, "assigned_to": 16}
    for i, col in enumerate(EXPORT_COLUMNS, start=1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = widths.get(col, 16)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
