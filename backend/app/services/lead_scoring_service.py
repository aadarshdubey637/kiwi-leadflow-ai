"""Transparent, rule-based lead scoring (0-100). The LLM never produces the score — it only supplies
the extracted facts; every point below is computed here and explained in plain text."""
from dataclasses import dataclass

from app.core.config import get_settings
from app.schemas.ai_analysis import AIExtraction

MAX = {"budget": 25, "clarity": 20, "urgency": 25, "relevance": 20, "engagement": 10}

# Budget tiers in INR: (minimum, points)
_BUDGET_TIERS = [(100_000, 25), (50_000, 20), (20_000, 15), (10_000, 10), (1, 5)]
_URGENCY_POINTS = {"High": 25, "Medium": 15, "Low": 5}


@dataclass
class ScoreBreakdown:
    budget: int
    clarity: int
    urgency: int
    relevance: int
    engagement: int
    total: int
    temperature: str
    explanation: str


def temperature_for(total: int) -> str:
    s = get_settings()
    if total >= s.hot_lead_threshold:
        return "Hot"
    if total >= s.warm_lead_threshold:
        return "Warm"
    return "Cold"


def _budget_points(ex: AIExtraction) -> tuple[int, str]:
    if ex.budget is None:
        return 0, "no budget stated"
    rates = get_settings().currency_to_inr
    cur = ex.currency or "INR"
    rate = rates.get(cur)
    assumed = ""
    if rate is None:
        rate, assumed = 1, f" (unknown currency {cur}, treated as INR)"
    elif ex.currency is None:
        assumed = " (currency not stated, treated as INR)"
    inr = ex.budget * rate
    for minimum, points in _BUDGET_TIERS:
        if inr >= minimum:
            return points, f"budget ≈ ₹{inr:,.0f}{assumed}"
    return 0, "budget is zero"


def calculate(ex: AIExtraction, category: str, has_email: bool, has_phone: bool, message: str) -> ScoreBreakdown:
    budget, b_note = _budget_points(ex)

    # A concrete need identified earns 6; each further requirement adds 2 (max 12). Weighting the first one most keeps
    # the score stable whether the model lists one combined requirement or four separate ones.
    clarity = 0 if not ex.requirements else min(6 + 2 * (len(ex.requirements) - 1), 12)
    clarity += 4 if ex.project_timeline else 0
    clarity += 4 if len(ex.missing_information) <= 2 else 0
    clarity = min(clarity, MAX["clarity"])
    c_note = f"{len(ex.requirements)} requirement(s), timeline {'given' if ex.project_timeline else 'missing'}, {len(ex.missing_information)} item(s) missing"

    urgency = _URGENCY_POINTS.get(ex.urgency or "", 0)
    u_note = f"urgency {ex.urgency or 'not stated'}"

    if category == "Other Services":
        relevance, r_note = 5, "does not match a core service"
    else:
        relevance = 10 + round(10 * ex.confidence)
        r_note = f"matches '{category}' (AI confidence {ex.confidence:.2f})"

    engagement = (3 if has_email else 0) + (3 if has_phone else 0)
    engagement += 2 if len(message.strip()) >= 100 else 0
    engagement += 2 if ex.customer_location else 0
    e_note = f"contact: {'email ' if has_email else ''}{'phone' if has_phone else ''}".strip() or "no contact details"

    total = budget + clarity + urgency + relevance + engagement
    temp = temperature_for(total)
    explanation = (
        f"Budget {budget}/{MAX['budget']} ({b_note}); Clarity {clarity}/{MAX['clarity']} ({c_note}); "
        f"Urgency {urgency}/{MAX['urgency']} ({u_note}); Relevance {relevance}/{MAX['relevance']} ({r_note}); "
        f"Engagement {engagement}/{MAX['engagement']} ({e_note}). Total {total}/100 → {temp} lead."
    )
    return ScoreBreakdown(budget, clarity, urgency, relevance, engagement, total, temp, explanation)
