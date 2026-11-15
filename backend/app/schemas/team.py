from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

Role = Literal["admin", "agent"]


class TeamMemberOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    open_enquiries: int  # assigned and still New / In Progress
    total_assigned: int
    created_at: datetime


class TeamMemberCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9._-]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    role: Role = "agent"

    @field_validator("username")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class TeamMemberUpdate(BaseModel):
    is_active: bool | None = None
    role: Role | None = None


class AssigneeUpdate(BaseModel):
    assignee_id: int | None = None  # null = unassign
