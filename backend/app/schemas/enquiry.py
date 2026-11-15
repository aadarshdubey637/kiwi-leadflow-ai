from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.schemas.ai_analysis import AnalysisOut
from app.schemas.communication import CommunicationOut
from app.utils.validators import normalize_phone

EnquiryStatus = Literal["New", "In Progress", "Converted", "Closed"]


class EnquiryCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=150)
    phone: str | None = None
    email: EmailStr | None = None
    message: str = Field(min_length=1, max_length=5000)
    source: str = Field(default="web", max_length=50)

    @field_validator("customer_name", "message")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v

    @field_validator("phone", mode="before")
    @classmethod
    def _phone(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        return normalize_phone(v)

    @model_validator(mode="after")
    def _need_contact(self):
        if not self.email and not self.phone:
            raise ValueError("Provide at least one of email or phone")
        return self


class EnquiryStatusUpdate(BaseModel):
    status: EnquiryStatus


class ResponseUpdate(BaseModel):
    edited_response: str = Field(min_length=1, max_length=3000)

    @field_validator("edited_response")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v


class EnquiryOut(BaseModel):
    """List-item shape: enquiry + the headline AI results the dashboard table needs."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    phone: str | None
    email: str | None
    message: str
    source: str
    status: str
    ai_status: str
    priority: str | None
    priority_reason: str | None
    needs_manual_review: bool
    duplicate_of_id: int | None
    duplicate_reason: str | None
    assigned_to_id: int | None
    assigned_to_name: str | None
    summary: str | None
    service_category: str | None
    lead_score_total: int | None
    lead_temperature: str | None
    created_at: datetime
    updated_at: datetime


class LeadScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_score: int
    budget_score: int
    requirement_clarity_score: int
    urgency_score: int
    service_relevance_score: int
    engagement_score: int
    lead_temperature: str
    scoring_explanation: str | None
    created_at: datetime


class ResponseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    generated_response: str
    edited_response: str | None
    final_response: str  # edited version if an admin edited it, else the AI original
    followup_questions: list[str]
    created_at: datetime
    updated_at: datetime


class FollowUpOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    suggested_action: str
    suggested_date: datetime | None
    status: str
    created_at: datetime


class EnquiryDetail(EnquiryOut):
    analysis: AnalysisOut | None
    lead_score: LeadScoreOut | None
    response: ResponseOut | None
    followups: list[FollowUpOut]
    communications: list[CommunicationOut]
