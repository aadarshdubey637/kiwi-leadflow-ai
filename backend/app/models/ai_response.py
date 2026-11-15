from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enquiry import utcnow


class AIResponse(Base):
    __tablename__ = "ai_responses"

    id: Mapped[int] = mapped_column(primary_key=True)
    enquiry_id: Mapped[int] = mapped_column(ForeignKey("enquiries.id", ondelete="CASCADE"), unique=True)
    generated_response: Mapped[str] = mapped_column(Text)  # original AI text, never overwritten by edits
    edited_response: Mapped[str | None] = mapped_column(Text)
    followup_questions: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    @property
    def final_response(self) -> str:
        return self.edited_response or self.generated_response

    enquiry = relationship("Enquiry", back_populates="response")
