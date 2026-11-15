from dataclasses import dataclass

from app.core.config import get_settings
from app.models.ai_analysis import SERVICE_CATEGORIES
from app.schemas.ai_analysis import AIExtraction


@dataclass
class Classification:
    category: str
    needs_manual_review: bool
    reason: str


def validate_category(category: str) -> str:
    """Hard gate: only the seven approved categories may ever reach the database."""
    if category not in SERVICE_CATEGORIES:
        raise ValueError(f"Unsupported service category: {category!r}")
    return category


def classify(extraction: AIExtraction) -> Classification:
    category = validate_category(extraction.service_category)
    threshold = get_settings().ai_low_confidence_threshold
    if category == "Other Services":
        return Classification(category, True, "No specific service matched; flagged for manual review")
    if extraction.confidence < threshold:
        return Classification(
            category, True, f"Category '{category}' assigned with low confidence ({extraction.confidence:.2f})"
        )
    return Classification(category, False, f"Matched '{category}' (confidence {extraction.confidence:.2f})")
