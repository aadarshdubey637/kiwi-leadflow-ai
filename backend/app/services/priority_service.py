from dataclasses import dataclass

from app.core.config import get_settings
from app.schemas.ai_analysis import AIExtraction

_LEVELS = ["Low", "Medium", "High"]


@dataclass
class PriorityResult:
    priority: str
    reason: str


def assign_priority(extraction: AIExtraction) -> PriorityResult:
    """Rule-based and explainable. Urgency drives priority; budget size alone never does.

    1. Start from the stated urgency (evidence-based, may be unknown).
    2. If urgency is unknown, a customer who describes a concrete need AND states a budget (with decent extraction
       confidence) looks ready to proceed -> Medium. This deliberately does not depend on HOW MANY requirements the
       model happened to split the request into (that varies between runs).
    3. If the AI is unsure (confidence below the review threshold), a "High" is capped at Medium until a person
       confirms it: low-confidence output, or a message that tried to steer the AI, must not jump the queue.
    4. Negative sentiment on an already-urgent request is noted but does not change the level.
    """
    low_confidence = extraction.confidence < get_settings().ai_low_confidence_threshold
    urgency = extraction.urgency
    if urgency:
        priority = urgency
        reason = f"Customer urgency is {urgency}."
        if priority == "High" and low_confidence:
            priority = "Medium"
            reason += f" Capped at Medium because the AI's confidence is low ({extraction.confidence:.2f}); a person should confirm."
    elif extraction.requirements and extraction.budget is not None and extraction.confidence >= 0.7:
        priority = "Medium"
        reason = "No urgency stated, but the customer described a concrete need and gave a budget (ready to proceed)."
    else:
        priority = "Low"
        reason = "No urgency stated and the request is not yet well defined."
    if extraction.sentiment == "Negative" and priority != "Low":
        reason += " Customer tone is negative; handle with care."
    assert priority in _LEVELS
    return PriorityResult(priority, reason)
