from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enquiry import utcnow


class WorkflowLog(Base):
    __tablename__ = "workflow_logs"
    __table_args__ = (
        CheckConstraint("execution_status IN ('started','success','failed','skipped')", name="ck_wf_status"),
        Index("ix_wf_enquiry_created", "enquiry_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    enquiry_id: Mapped[int] = mapped_column(ForeignKey("enquiries.id", ondelete="CASCADE"))
    workflow_step: Mapped[str] = mapped_column(String(80))
    execution_status: Mapped[str] = mapped_column(String(10))
    message: Mapped[str | None] = mapped_column(Text)  # error info lives here when failed
    execution_time: Mapped[float | None] = mapped_column(Float)  # seconds
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    enquiry = relationship("Enquiry", back_populates="workflow_logs")
