from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.ai_analysis import SERVICE_CATEGORIES

ServiceCategory = Literal[
    "Website Development",
    "Mobile Application Development",
    "AI Software Development",
    "Digital Marketing",
    "E-commerce Development",
    "Custom Software Development",
    "Other Services",
]
_CATEGORY_LOOKUP = {c.casefold(): c for c in SERVICE_CATEGORIES}


def _none_if_blank(v):
    if isinstance(v, str) and (not v.strip() or v.strip().lower() in {"null", "none", "n/a", "unknown"}):
        return None
    return v.strip() if isinstance(v, str) else v


def _clean_list(v, max_items: int = 12, max_len: int = 200):
    if v is None:
        return []
    if not isinstance(v, list):
        raise ValueError("must be a list")
    out, seen = [], set()
    for item in v:
        if not isinstance(item, str):
            continue
        item = item.strip()[:max_len]
        if item and item.casefold() not in seen:
            seen.add(item.casefold())
            out.append(item)
    return out[:max_items]


class AIExtraction(BaseModel):
    """Contract for the LLM's structured output. Anything outside it is rejected, not repaired."""

    service_category: ServiceCategory
    budget: float | None = Field(default=None, ge=0)
    currency: str | None = None
    customer_location: str | None = Field(default=None, max_length=150)
    urgency: Literal["Low", "Medium", "High"] | None = None
    project_timeline: str | None = Field(default=None, max_length=150)
    requirements: list[str] = []
    missing_information: list[str] = []
    intent: str = Field(min_length=1, max_length=200)
    sentiment: Literal["Positive", "Neutral", "Negative"]
    language: str = Field(min_length=1, max_length=50)
    summary: str = Field(min_length=1, max_length=600)
    confidence: float = Field(ge=0, le=1)

    @field_validator("service_category", mode="before")
    @classmethod
    def _category(cls, v):
        # Accept harmless case/whitespace differences, but never arbitrary categories.
        if isinstance(v, str):
            return _CATEGORY_LOOKUP.get(v.strip().casefold(), v)
        return v

    @field_validator("urgency", "sentiment", mode="before")
    @classmethod
    def _title(cls, v):
        v = _none_if_blank(v)
        return v.capitalize() if isinstance(v, str) else v

    @field_validator("currency", mode="before")
    @classmethod
    def _currency(cls, v):
        v = _none_if_blank(v)
        if v is None:
            return None
        v = str(v).strip().upper()
        if len(v) != 3 or not v.isalpha():
            raise ValueError("currency must be a 3-letter ISO code")
        return v

    @field_validator("customer_location", "project_timeline", mode="before")
    @classmethod
    def _blank_to_none(cls, v):
        return _none_if_blank(v)

    @field_validator("budget", mode="before")
    @classmethod
    def _budget(cls, v):
        if isinstance(v, str):
            v = _none_if_blank(v)
            if v is not None:
                v = v.replace(",", "")
        return v

    @field_validator("requirements", "missing_information", mode="before")
    @classmethod
    def _lists(cls, v):
        return _clean_list(v)


class AnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    service_category: str
    customer_location: str | None
    budget: float | None
    currency: str | None
    urgency: str | None
    project_timeline: str | None
    project_requirements: list[str]
    missing_information: list[str]
    summary: str | None
    customer_intent: str | None
    sentiment: str | None
    detected_language: str | None
    confidence_score: float | None
    created_at: datetime
