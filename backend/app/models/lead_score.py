from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enquiry import utcnow


class LeadScore(Base):
    __tablename__ = "lead_scores"
    __table_args__ = (
        CheckConstraint("total_score BETWEEN 0 AND 100", name="ck_score_total"),
        CheckConstraint("lead_temperature IN ('Hot','Warm','Cold')", name="ck_score_temp"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    enquiry_id: Mapped[int] = mapped_column(ForeignKey("enquiries.id", ondelete="CASCADE"), unique=True)
    total_score: Mapped[int] = mapped_column(Integer)
    budget_score: Mapped[int] = mapped_column(Integer)  # max 25
    requirement_clarity_score: Mapped[int] = mapped_column(Integer)  # max 20
    urgency_score: Mapped[int] = mapped_column(Integer)  # max 25
    service_relevance_score: Mapped[int] = mapped_column(Integer)  # max 20
    engagement_score: Mapped[int] = mapped_column(Integer)  # max 10
    lead_temperature: Mapped[str] = mapped_column(String(10), index=True)
    scoring_explanation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    enquiry = relationship("Enquiry", back_populates="lead_score")
