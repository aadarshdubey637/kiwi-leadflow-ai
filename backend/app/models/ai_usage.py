from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.enquiry import utcnow


class AIUsage(Base):
    """One row per LLM call attempt (including failures and retries)."""

    __tablename__ = "ai_usage"
    __table_args__ = (
        CheckConstraint("execution_status IN ('success','failed')", name="ck_usage_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # SET NULL: usage/cost history must survive even if an enquiry is deleted
    enquiry_id: Mapped[int | None] = mapped_column(ForeignKey("enquiries.id", ondelete="SET NULL"), index=True)
    provider: Mapped[str] = mapped_column(String(20), index=True)
    model_name: Mapped[str] = mapped_column(String(80))
    task: Mapped[str] = mapped_column(String(40), default="extraction")  # extraction | response
    attempt: Mapped[int] = mapped_column(Integer, default=1)  # attempt > 1 means a retry
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    response_time: Mapped[float] = mapped_column(Float, default=0.0)  # seconds
    estimated_cost: Mapped[float] = mapped_column(Numeric(10, 6), default=0)  # USD, estimate only
    execution_status: Mapped[str] = mapped_column(String(10))
    error_message: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
