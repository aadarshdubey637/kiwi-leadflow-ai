from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, Float, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enquiry import utcnow

SERVICE_CATEGORIES = (
    "Website Development",
    "Mobile Application Development",
    "AI Software Development",
    "Digital Marketing",
    "E-commerce Development",
    "Custom Software Development",
    "Other Services",
)


class AIAnalysis(Base):
    __tablename__ = "ai_analysis"
    __table_args__ = (
        CheckConstraint(
            "service_category IN ('Website Development','Mobile Application Development',"
            "'AI Software Development','Digital Marketing','E-commerce Development',"
            "'Custom Software Development','Other Services')",
            name="ck_analysis_category",
        ),
        CheckConstraint("confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)", name="ck_analysis_conf"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # unique => one analysis per enquiry; retries update the row instead of duplicating it
    enquiry_id: Mapped[int] = mapped_column(ForeignKey("enquiries.id", ondelete="CASCADE"), unique=True)
    service_category: Mapped[str] = mapped_column(String(50), index=True)
    customer_location: Mapped[str | None] = mapped_column(String(150))
    budget: Mapped[float | None] = mapped_column(Numeric(14, 2))
    currency: Mapped[str | None] = mapped_column(String(3))
    urgency: Mapped[str | None] = mapped_column(String(10))
    project_timeline: Mapped[str | None] = mapped_column(String(150))
    project_requirements: Mapped[list] = mapped_column(JSON, default=list)
    missing_information: Mapped[list] = mapped_column(JSON, default=list)
    summary: Mapped[str | None] = mapped_column(Text)
    customer_intent: Mapped[str | None] = mapped_column(String(200))
    sentiment: Mapped[str | None] = mapped_column(String(20))
    detected_language: Mapped[str | None] = mapped_column(String(50))
    confidence_score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    enquiry = relationship("Enquiry", back_populates="analysis")
