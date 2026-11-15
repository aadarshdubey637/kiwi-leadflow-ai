import csv
import io

from sqlalchemy import select

from app.models import Enquiry
from app.services.providers.base import ProviderUnavailable
from app.tests.conftest import DEFAULT_EXTRACTION


def seed(client, submit, fake):
    """3 enquiries: e-commerce/High/converted, website/Low, mobile/Medium."""
    fake.extraction = {**DEFAULT_EXTRACTION, "urgency": "High"}
    a = submit(email="a@example.com", phone="+919000000001", message="Need e-commerce site Indore Budget 50000 INR urgent")
    fake.extraction = {**DEFAULT_EXTRACTION, "service_category": "Website Development", "urgency": "Low",
                       "budget": None, "currency": None, "customer_location": None}
    b = submit(email="b@example.com", phone="+919000000002", message="Need a company website, no hurry at all")
    fake.extraction = {**DEFAULT_EXTRACTION, "service_category": "Mobile Application Development",
                       "budget": 20000, "currency": "USD", "customer_location": None}
    c = submit(email="c@example.com", phone="+919000000003", message="Mobile app for deliveries, budget 20000 USD maybe")
    client.put(f"/api/enquiries/{a}/status", json={"status": "Converted"})
    client.put(f"/api/enquiries/{c}/status", json={"status": "In Progress"})
    return a, b, c


def test_dashboard_stats_counts(client, submit, fake):
    seed(client, submit, fake)
    d = client.get("/api/dashboard/stats").json()["data"]
    assert d["total_enquiries"] == 3 and d["new_enquiries"] == 1
    assert d["high_priority_enquiries"] == 1 and d["in_progress_enquiries"] == 1 and d["converted_enquiries"] == 1


def test_empty_database_stats(client):
    d = client.get("/api/dashboard/stats").json()["data"]
    assert d["total_enquiries"] == 0
    assert client.get("/api/analytics/conversion").json()["data"]["conversion_rate"] == 0
    assert client.get("/api/analytics/leads").json()["data"]["average_score"] is None


def test_category_distribution_lists_all_seven(client, submit, fake):
    seed(client, submit, fake)
    items = client.get("/api/dashboard/categories").json()["data"]
    by = {i["label"]: i for i in items}
    assert len(items) == 7
    assert by["E-commerce Development"]["count"] == 1 and by["Website Development"]["count"] == 1
    assert by["Mobile Application Development"]["count"] == 1 and by["Digital Marketing"]["count"] == 0
    assert round(by["Website Development"]["percentage"], 1) == 33.3


def test_priority_distribution(client, submit, fake):
    seed(client, submit, fake)
    by = {i["label"]: i["count"] for i in client.get("/api/dashboard/priorities").json()["data"]}
    assert by["High"] == 1 and by["Low"] == 1 and by["Medium"] == 1


def test_lead_distribution(client, submit, fake):
    seed(client, submit, fake)
    d = client.get("/api/analytics/leads").json()["data"]
    assert d["hot"] + d["warm"] + d["cold"] == 3 and d["unscored"] == 0
    assert 0 < d["average_score"] <= 100 and sum(b["count"] for b in d["score_buckets"]) == 3


def test_conversion_statistics(client, submit, fake):
    seed(client, submit, fake)
    d = client.get("/api/analytics/conversion").json()["data"]
    assert d["total_enquiries"] == 3 and d["converted"] == 1 and d["conversion_rate"] == 33.3 and d["open"] == 2
    assert sum(t["converted"] for t in d["by_temperature"]) == 1


def test_funnel_stages_are_monotonic(client, submit, fake):
    seed(client, submit, fake)
    f = client.get("/api/analytics/funnel").json()["data"]
    counts = [s["count"] for s in f]
    assert counts[0] == 3 and counts[1] == 3 and counts[-1] == 1 and counts[3] == 2
    assert counts == sorted(counts, reverse=True)


def test_funnel_counts_failed_ai_as_not_analysed(client, submit, fake):
    fake.script["extraction"] = [ProviderUnavailable("x")] * 3
    submit()
    f = client.get("/api/analytics/funnel").json()["data"]
    assert f[0]["count"] == 1 and f[1]["count"] == 0
    assert client.get("/api/dashboard/stats").json()["data"]["ai_failed"] == 1


def test_trends(client, submit, fake):
    seed(client, submit, fake)
    for period in ("daily", "weekly", "monthly"):
        pts = client.get(f"/api/analytics/trends?period={period}&days=30").json()["data"]
        assert sum(p["count"] for p in pts) == 3
    assert client.get("/api/analytics/trends?period=hourly").status_code == 422


def test_pipeline_value_by_currency_never_mixed(client, submit, fake):
    seed(client, submit, fake)
    d = client.get("/api/analytics/pipeline").json()["data"]
    by = {p["currency"]: p for p in d["by_currency"]}
    # a (INR 50000) is Converted so excluded; c (USD 20000) is open; b has no budget
    assert by == {"USD": {"currency": "USD", "enquiries": 1, "estimated_pipeline_value": 20000.0}}
    assert d["open_enquiries_without_budget"] == 1 and "NOT actual" in d["note"]


# ---------- search / filters / export ----------

def test_filters_and_search(client, submit, fake):
    seed(client, submit, fake)
    q = lambda s: client.get(f"/api/enquiries?{s}").json()
    assert q("category=Website Development")["meta"]["total"] == 1
    assert q("priority=High")["meta"]["total"] == 1
    assert q("status=Converted")["meta"]["total"] == 1
    assert q("search=deliveries")["meta"]["total"] == 1
    assert q("search=%25")["meta"]["total"] == 0  # LIKE wildcards are escaped
    assert q("ai_status=completed")["meta"]["total"] == 3
    assert q("temperature=Hot")["meta"]["total"] + q("temperature=Warm")["meta"]["total"] + q("temperature=Cold")["meta"]["total"] == 3
    row = q("page_size=1")["data"][0]
    assert row["service_category"] and row["lead_temperature"] and row["lead_score_total"] is not None
    assert client.get("/api/enquiries?category=Nonsense").status_code == 422
    assert client.get("/api/enquiries?page_size=1000").status_code == 422


def test_csv_export(client, submit, fake):
    seed(client, submit, fake)
    r = client.get("/api/enquiries/export?status=Converted")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers["content-disposition"]
    rows = list(csv.DictReader(io.StringIO(r.text)))
    assert len(rows) == 1 and rows[0]["service_category"] == "E-commerce Development"
    assert rows[0]["phone"].startswith("+91") and rows[0]["lead_temperature"]
    assert len(list(csv.DictReader(io.StringIO(client.get("/api/enquiries/export").text)))) == 3


def test_csv_formula_injection_is_neutralised(client, submit, fake):
    submit(customer_name="=HYPERLINK(\"http://evil\",\"x\")")
    text = client.get("/api/enquiries/export").text
    assert "'=HYPERLINK" in text and ",=HYPERLINK" not in text


# ---------- monitoring ----------

def test_ai_usage_and_performance(client, submit, fake):
    fake.script["extraction"] = [ProviderUnavailable("x"), DEFAULT_EXTRACTION]  # 1 failure + 1 retry success
    submit()
    u = client.get("/api/monitoring/ai-usage").json()["data"]
    assert (u["total_requests"], u["successful_requests"], u["failed_requests"], u["retry_count"]) == (3, 2, 1, 1)
    assert u["input_tokens"] == 200 and u["output_tokens"] == 100
    assert u["by_provider"][0]["provider"] == "fake" and "estimates" in u["cost_note"]
    p = client.get("/api/monitoring/performance").json()["data"]
    assert p["workflows_completed"] == 1 and p["workflows_failed"] == 0 and p["workflow_success_rate"] == 100
    assert round(p["ai_success_rate"], 1) == 66.7


def test_pipeline_excludes_flagged_duplicates(client, submit, fake):
    submit()  # INR 50000
    submit(phone="+919333333333", message="completely different text about something else entirely")  # same email -> duplicate
    d = client.get("/api/analytics/pipeline").json()["data"]
    assert d["by_currency"] == [{"currency": "INR", "enquiries": 1, "estimated_pipeline_value": 50000.0}]
