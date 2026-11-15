from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enquiry import utcnow


class FollowUp(Base):
    __tablename__ = "followups"
    __table_args__ = (
        CheckConstraint("status IN ('Pending','Done','Dismissed')", name="ck_followup_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    enquiry_id: Mapped[int] = mapped_column(ForeignKey("enquiries.id", ondelete="CASCADE"), index=True)
    suggested_action: Mapped[str] = mapped_column(Text)
    suggested_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(10), default="Pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    enquiry = relationship("Enquiry", back_populates="followups")
