from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

ENQUIRY_STATUSES = ("New", "In Progress", "Converted", "Closed")
AI_STATUSES = ("pending", "processing", "completed", "failed")
PRIORITIES = ("Low", "Medium", "High")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Enquiry(Base):
    __tablename__ = "enquiries"
    __table_args__ = (
        CheckConstraint("status IN ('New','In Progress','Converted','Closed')", name="ck_enquiry_status"),
        CheckConstraint("ai_status IN ('pending','processing','completed','failed')", name="ck_enquiry_ai_status"),
        CheckConstraint("priority IS NULL OR priority IN ('Low','Medium','High')", name="ck_enquiry_priority"),
        Index("ix_enquiries_status_created", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(150))
    phone: Mapped[str | None] = mapped_column(String(20), index=True)
    email: Mapped[str | None] = mapped_column(String(254), index=True)
    message: Mapped[str] = mapped_column(Text)  # original text, never modified
    source: Mapped[str] = mapped_column(String(50), default="web")
    status: Mapped[str] = mapped_column(String(20), default="New")

    # AI processing state — lets us keep the enquiry even if the LLM fails, and retry later.
    ai_status: Mapped[str] = mapped_column(String(20), default="pending")
    priority: Mapped[str | None] = mapped_column(String(10), index=True)
    priority_reason: Mapped[str | None] = mapped_column(Text)
    needs_manual_review: Mapped[bool] = mapped_column(Boolean, default=False)

    # Team assignment (set automatically at creation, changeable by admins)
    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id", ondelete="SET NULL"), index=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Duplicate detection: flagged for admin review, never merged/deleted automatically.
    duplicate_of_id: Mapped[int | None] = mapped_column(ForeignKey("enquiries.id", ondelete="SET NULL"))
    duplicate_reason: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Convenience read-only values used by list/export endpoints.
    @property
    def assigned_to_name(self) -> str | None:
        return self.assignee.username if self.assignee else None

    @property
    def summary(self) -> str | None:
        return self.analysis.summary if self.analysis else None

    @property
    def service_category(self) -> str | None:
        return self.analysis.service_category if self.analysis else None

    @property
    def lead_score_total(self) -> int | None:
        return self.lead_score.total_score if self.lead_score else None

    @property
    def lead_temperature(self) -> str | None:
        return self.lead_score.lead_temperature if self.lead_score else None

    assignee = relationship("AdminUser", foreign_keys=[assigned_to_id], lazy="joined")
    communications = relationship("Communication", back_populates="enquiry", cascade="all, delete-orphan", order_by="Communication.id.desc()")
    analysis = relationship("AIAnalysis", back_populates="enquiry", uselist=False, cascade="all, delete-orphan")
    response = relationship("AIResponse", back_populates="enquiry", uselist=False, cascade="all, delete-orphan")
    lead_score = relationship("LeadScore", back_populates="enquiry", uselist=False, cascade="all, delete-orphan")
    workflow_logs = relationship("WorkflowLog", back_populates="enquiry", cascade="all, delete-orphan")
    followups = relationship("FollowUp", back_populates="enquiry", cascade="all, delete-orphan")
