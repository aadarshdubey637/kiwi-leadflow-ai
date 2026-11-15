from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.enquiry import utcnow


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))  # never plain text
    role: Mapped[str] = mapped_column(String(20), default="admin")  # admin | agent
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")  # inactive members receive no new enquiries
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
