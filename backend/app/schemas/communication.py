from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommunicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel: str
    kind: str
    recipient: str
    subject: str | None
    body: str | None
    status: str
    error: str | None
    sent_by_name: str | None
    created_at: datetime


class SendEmailRequest(BaseModel):
    """Both optional: by default the enquiry's current reply (edited version if any) is sent."""

    subject: str | None = Field(default=None, max_length=300)
    body: str | None = Field(default=None, max_length=3000)


class WhatsAppRequest(BaseModel):
    text: str | None = Field(default=None, max_length=3000)


class WhatsAppOut(BaseModel):
    link: str
    communication: CommunicationOut


class CapabilitiesOut(BaseModel):
    email_enabled: bool
    whatsapp_enabled: bool
    default_country_code: str
