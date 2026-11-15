from datetime import datetime
from typing import Literal

from pydantic import BaseModel

FollowUpStatus = Literal["Pending", "Done", "Dismissed"]


class FollowUpItem(BaseModel):
    id: int
    enquiry_id: int
    customer_name: str
    enquiry_priority: str | None
    lead_temperature: str | None
    assigned_to_name: str | None
    suggested_action: str
    suggested_date: datetime | None
    status: str
    is_overdue: bool  # pending and past its suggested date
    created_at: datetime


class FollowUpSummary(BaseModel):
    pending: int
    overdue: int
    due_today: int
    done: int


class FollowUpUpdate(BaseModel):
    status: FollowUpStatus
