import pytest

from app.schemas.ai_analysis import AIExtraction
from app.services import (
    classification_service, duplicate_service, followup_service, lead_scoring_service, priority_service,
)
from app.tests.conftest import DEFAULT_EXTRACTION


def ex(**kw) -> AIExtraction:
    return AIExtraction.model_validate({**DEFAULT_EXTRACTION, **kw})


# ---------- classification ----------

def test_confident_category_needs_no_review():
    c = classification_service.classify(ex())
    assert c.category == "E-commerce Development" and not c.needs_manual_review


def test_low_confidence_flags_manual_review():
    assert classification_service.classify(ex(confidence=0.3)).needs_manual_review


def test_other_services_flags_manual_review():
    c = classification_service.classify(ex(service_category="Other Services"))
    assert c.category == "Other Services" and c.needs_manual_review


def test_category_gate_rejects_unknown():
    with pytest.raises(ValueError):
        classification_service.validate_category("Blockchain")


# ---------- priority ----------

@pytest.mark.parametrize("urgency,expected", [("High", "High"), ("Medium", "Medium"), ("Low", "Low")])
def test_priority_follows_urgency(urgency, expected):
    assert priority_service.assign_priority(ex(urgency=urgency)).priority == expected


def test_big_budget_does_not_mean_high_priority():
    p = priority_service.assign_priority(ex(urgency=None, budget=10_000_000, requirements=[], confidence=0.5))
    assert p.priority == "Low" and p.reason


def test_unknown_urgency_but_well_defined_request_is_medium():
    assert priority_service.assign_priority(ex(urgency=None)).priority == "Medium"


# ---------- lead scoring ----------

def score(**kw):
    return lead_scoring_service.calculate(ex(**kw), kw.get("service_category", "E-commerce Development"),
                                          True, True, "x" * 120)


def test_score_breakdown_adds_up_and_is_bounded():
    s = score()
    assert s.total == s.budget + s.clarity + s.urgency + s.relevance + s.engagement
    assert 0 <= s.total <= 100 and "Total" in s.explanation
    assert s.budget <= 25 and s.clarity <= 20 and s.urgency <= 25 and s.relevance <= 20 and s.engagement <= 10


def test_hot_lead_and_cold_lead():
    hot = score(budget=500000, urgency="High", missing_information=[], project_timeline="1 month", confidence=0.95)
    assert hot.temperature == "Hot" and hot.total >= 80
    cold = lead_scoring_service.calculate(
        ex(budget=None, currency=None, urgency=None, requirements=[], service_category="Other Services",
           confidence=0.2, customer_location=None, missing_information=["a", "b", "c"]),
        "Other Services", False, True, "hi")
    assert cold.temperature == "Cold" and cold.total < 50


@pytest.mark.parametrize("total,temp", [(100, "Hot"), (80, "Hot"), (79, "Warm"), (50, "Warm"), (49, "Cold"), (0, "Cold")])
def test_temperature_boundaries(total, temp):
    assert lead_scoring_service.temperature_for(total) == temp


def test_budget_currency_conversion_and_unknown_currency_noted():
    usd = score(budget=1000, currency="USD")  # ≈ ₹83,000
    assert usd.budget == 20
    unknown = score(budget=500000, currency=None)
    assert "treated as INR" in unknown.explanation


# ---------- duplicates ----------

def test_text_similarity():
    a = "I need an e-commerce website for my shop in Indore"
    assert duplicate_service.similarity(a, a.upper() + "!!") == 1.0
    assert duplicate_service.similarity(a, "Looking for a mobile app for food delivery") < 0.5


# ---------- follow-ups ----------

def test_followups_for_hot_high_priority_with_missing_info():
    f = followup_service.suggest("New", "High", "Hot", ["Project timeline"])
    actions = " | ".join(x.action for x in f)
    assert "high-priority" in actions and "missing project details" in actions and "interested customer" in actions


def test_no_followups_for_closed_or_converted():
    assert followup_service.suggest("Closed", "High", "Hot", ["x"]) == []
    assert followup_service.suggest("Converted", "Low", "Cold", []) == []


def test_manual_review_followup():
    assert any("Manually review" in x.action for x in followup_service.suggest("New", "Low", "Cold", [], True))


# ---------- robustness: priority/score must not depend on how the model splits requirements, or on injected text ----------
def test_priority_medium_for_one_combined_requirement_plus_budget():
    """The assignment's own example: the model may return 1 long requirement or 4 short ones; both mean 'ready to proceed'."""
    one = priority_service.assign_priority(ex(urgency=None, requirements=["e-commerce website with browsing, orders and payments"]))
    four = priority_service.assign_priority(ex(urgency=None, requirements=["Browsing", "Orders", "Payments", "Website"]))
    assert one.priority == four.priority == "Medium"


def test_priority_low_without_a_concrete_need_or_without_budget():
    assert priority_service.assign_priority(ex(urgency=None, requirements=[])).priority == "Low"
    assert priority_service.assign_priority(ex(urgency=None, budget=None, currency=None)).priority == "Low"


def test_high_priority_is_capped_when_ai_confidence_is_low():
    p = priority_service.assign_priority(ex(urgency="High", confidence=0.28))
    assert p.priority == "Medium" and "confidence is low" in p.reason
    assert priority_service.assign_priority(ex(urgency="High", confidence=0.9)).priority == "High"  # normal case unchanged


def test_clarity_score_is_stable_across_requirement_granularity():
    base = dict(missing_information=[], project_timeline="1 month")
    one = lead_scoring_service.calculate(ex(requirements=["one long combined requirement"], **base), "E-commerce Development", True, True, "x" * 120)
    four = lead_scoring_service.calculate(ex(requirements=["a", "b", "c", "d"], **base), "E-commerce Development", True, True, "x" * 120)
    assert (one.clarity, four.clarity) == (14, 20)  # 6+4+4 vs 12+4+4 (capped at 20): a gap of 6, not the old 3-vs-12 swing
