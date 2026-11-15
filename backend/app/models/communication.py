from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enquiry import utcnow


class Communication(Base):
    """Audit trail of everything the system sent (or prepared to send) about an enquiry."""

    __tablename__ = "communications"
    __table_args__ = (
        CheckConstraint("channel IN ('email','whatsapp')", name="ck_comm_channel"),
        CheckConstraint("kind IN ('customer_reply','team_notification')", name="ck_comm_kind"),
        # 'opened' = WhatsApp click-to-chat was opened by the admin; we cannot know if they pressed send
        CheckConstraint("status IN ('sent','failed','opened','skipped')", name="ck_comm_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    enquiry_id: Mapped[int] = mapped_column(ForeignKey("enquiries.id", ondelete="CASCADE"), index=True)
    channel: Mapped[str] = mapped_column(String(10))
    kind: Mapped[str] = mapped_column(String(20))
    recipient: Mapped[str] = mapped_column(String(400))
    subject: Mapped[str | None] = mapped_column(String(300))
    body: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(10))
    error: Mapped[str | None] = mapped_column(String(300))
    sent_by_id: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    enquiry = relationship("Enquiry", back_populates="communications")
    sent_by = relationship("AdminUser", foreign_keys=[sent_by_id], lazy="joined")

    @property
    def sent_by_name(self) -> str | None:
        return self.sent_by.username if self.sent_by else None
