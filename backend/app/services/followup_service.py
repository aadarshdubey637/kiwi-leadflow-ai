from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class FollowUpSuggestion:
    action: str
    due: datetime


def suggest(
    enquiry_status: str, priority: str, temperature: str, missing_information: list[str],
    needs_manual_review: bool = False, now: datetime | None = None,
) -> list[FollowUpSuggestion]:
    """Rule-based follow-up actions. Suggestions only — nothing is sent or scheduled externally."""
    now = now or datetime.now(timezone.utc)
    if enquiry_status in ("Converted", "Closed"):
        return []

    out: list[FollowUpSuggestion] = []
    if needs_manual_review:
        out.append(FollowUpSuggestion("Manually review this enquiry — the AI could not classify it confidently", now + timedelta(days=1)))
    if priority == "High":
        out.append(FollowUpSuggestion("Review this high-priority enquiry and respond immediately", now + timedelta(hours=4)))
    if missing_information:
        items = ", ".join(missing_information[:5])
        out.append(FollowUpSuggestion(f"Request missing project details: {items}", now + timedelta(days=1)))
    if temperature == "Hot":
        out.append(FollowUpSuggestion("Contact this interested customer and propose a call", now + timedelta(days=1)))
    elif temperature == "Warm":
        out.append(FollowUpSuggestion("Schedule a follow-up conversation to qualify the requirement", now + timedelta(days=3)))
    else:
        out.append(FollowUpSuggestion("Send a nurturing message and check interest later", now + timedelta(days=7)))
    if enquiry_status == "New" and temperature != "Cold" and priority != "High":
        out.append(FollowUpSuggestion("Move enquiry to In Progress once the customer has been contacted", now + timedelta(days=2)))
    return out
