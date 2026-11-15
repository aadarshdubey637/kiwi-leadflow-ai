"""Read-only reporting queries for the dashboard, analytics and monitoring endpoints."""
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AIAnalysis, AIUsage, Enquiry, LeadScore, WorkflowLog
from app.models.ai_analysis import SERVICE_CATEGORIES

PIPELINE_NOTE = (
    "Estimated pipeline value is the sum of budgets customers STATED in open enquiries. "
    "It is NOT actual or expected revenue, and currencies are never converted or mixed."
)


def _pct(part: int, whole: int) -> float:
    return round(100 * part / whole, 1) if whole else 0.0


def _count(db: Session, *conditions) -> int:
    return db.scalar(select(func.count()).select_from(Enquiry).where(*conditions)) or 0


# ---------- dashboard ----------

def dashboard_stats(db: Session) -> dict:
    return {
        "total_enquiries": _count(db),
        "new_enquiries": _count(db, Enquiry.status == "New"),
        "high_priority_enquiries": _count(db, Enquiry.priority == "High"),
        "in_progress_enquiries": _count(db, Enquiry.status == "In Progress"),
        "converted_enquiries": _count(db, Enquiry.status == "Converted"),
        "closed_enquiries": _count(db, Enquiry.status == "Closed"),
        "needs_manual_review": _count(db, Enquiry.needs_manual_review.is_(True)),
        "ai_failed": _count(db, Enquiry.ai_status == "failed"),
    }


def category_distribution(db: Session) -> list[dict]:
    """All seven categories always appear (count 0 if unused); unanalysed enquiries are listed separately."""
    rows = dict(db.execute(select(AIAnalysis.service_category, func.count()).group_by(AIAnalysis.service_category)).all())
    total = _count(db)
    unanalysed = total - sum(rows.values())
    items = [(c, rows.get(c, 0)) for c in SERVICE_CATEGORIES]
    if unanalysed:
        items.append(("Not yet analysed", unanalysed))
    return [{"label": label, "count": n, "percentage": _pct(n, total)} for label, n in items]


def priority_distribution(db: Session) -> list[dict]:
    rows = dict(db.execute(select(Enquiry.priority, func.count()).group_by(Enquiry.priority)).all())
    total = _count(db)
    items = [(p, rows.get(p, 0)) for p in ("High", "Medium", "Low")]
    if rows.get(None):
        items.append(("Not yet assigned", rows[None]))
    return [{"label": label, "count": n, "percentage": _pct(n, total)} for label, n in items]


# ---------- analytics ----------

def lead_distribution(db: Session) -> dict:
    temps = dict(db.execute(select(LeadScore.lead_temperature, func.count()).group_by(LeadScore.lead_temperature)).all())
    scores = db.scalars(select(LeadScore.total_score)).all()
    scored = len(scores)
    buckets = Counter(min(s // 20, 4) for s in scores)
    labels = ["0-19", "20-39", "40-59", "60-79", "80-100"]
    return {
        "hot": temps.get("Hot", 0), "warm": temps.get("Warm", 0), "cold": temps.get("Cold", 0),
        "unscored": _count(db) - scored,
        "average_score": round(sum(scores) / scored, 1) if scored else None,
        "score_buckets": [{"label": labels[i], "count": buckets.get(i, 0), "percentage": _pct(buckets.get(i, 0), scored)}
                          for i in range(5)],
    }


def conversion_stats(db: Session) -> dict:
    total = _count(db)
    converted, closed = _count(db, Enquiry.status == "Converted"), _count(db, Enquiry.status == "Closed")
    by_temp = []
    for temp in ("Hot", "Warm", "Cold"):
        n = db.scalar(select(func.count()).select_from(LeadScore).where(LeadScore.lead_temperature == temp)) or 0
        conv = db.scalar(
            select(func.count()).select_from(LeadScore).join(Enquiry, Enquiry.id == LeadScore.enquiry_id)
            .where(LeadScore.lead_temperature == temp, Enquiry.status == "Converted")
        ) or 0
        by_temp.append({"temperature": temp, "enquiries": n, "converted": conv, "conversion_rate": _pct(conv, n)})
    return {
        "total_enquiries": total, "converted": converted, "closed": closed,
        "open": total - converted - closed, "conversion_rate": _pct(converted, total), "by_temperature": by_temp,
    }


def funnel(db: Session) -> list[dict]:
    total = _count(db)
    analysed = _count(db, Enquiry.ai_status == "completed")
    qualified = db.scalar(
        select(func.count()).select_from(LeadScore).where(LeadScore.lead_temperature.in_(("Hot", "Warm")))
    ) or 0
    engaged = _count(db, Enquiry.status.in_(("In Progress", "Converted")))
    converted = _count(db, Enquiry.status == "Converted")
    stages = [("Enquiries received", total), ("AI analysed", analysed), ("Qualified (Hot/Warm)", qualified),
              ("Engaged (In Progress/Converted)", engaged), ("Converted", converted)]
    return [{"stage": s, "count": n, "percentage_of_total": _pct(n, total)} for s, n in stages]


def trends(db: Session, period: str, days: int) -> list[dict]:
    """Bucket in Python (portable across SQLite/PostgreSQL). Empty periods are included as zero."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    created = db.scalars(select(Enquiry.created_at).where(Enquiry.created_at >= since)).all()

    def bucket(d: datetime) -> str:
        if period == "monthly":
            return d.strftime("%Y-%m")
        if period == "weekly":
            return (d.date() - timedelta(days=d.weekday())).isoformat()  # Monday of that week
        return d.date().isoformat()

    counts = Counter(bucket(d) for d in created)
    keys, cursor, end = [], since, datetime.now(timezone.utc)
    step = timedelta(days=1)
    while cursor <= end:
        k = bucket(cursor)
        if k not in keys:
            keys.append(k)
        cursor += step
    return [{"period": k, "count": counts.get(k, 0)} for k in keys]


def pipeline_value(db: Session) -> dict:
    rows = db.execute(
        select(AIAnalysis.currency, func.count(), func.sum(AIAnalysis.budget))
        .join(Enquiry, Enquiry.id == AIAnalysis.enquiry_id)
        .where(Enquiry.status.in_(("New", "In Progress")), AIAnalysis.budget.is_not(None),
               Enquiry.duplicate_of_id.is_(None))  # flagged duplicates must not double-count a budget
        .group_by(AIAnalysis.currency)
    ).all()
    no_budget = db.scalar(
        select(func.count()).select_from(Enquiry).outerjoin(AIAnalysis, AIAnalysis.enquiry_id == Enquiry.id)
        .where(Enquiry.status.in_(("New", "In Progress")), AIAnalysis.budget.is_(None),
               Enquiry.duplicate_of_id.is_(None))
    ) or 0
    return {
        "note": PIPELINE_NOTE,
        "by_currency": [{"currency": c or "Unspecified", "enquiries": n, "estimated_pipeline_value": float(total or 0)}
                        for c, n, total in rows],
        "open_enquiries_without_budget": no_budget,
    }


# ---------- monitoring ----------

def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 3) if values else 0.0


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return round(ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))], 3)


def ai_usage_stats(db: Session) -> dict:
    rows = db.scalars(select(AIUsage)).all()
    groups: dict[tuple[str, str], list[AIUsage]] = defaultdict(list)
    for r in rows:
        groups[(r.provider, r.model_name)].append(r)
    by_provider = []
    for (provider, model), items in sorted(groups.items()):
        by_provider.append({
            "provider": provider, "model_name": model, "requests": len(items),
            "successful": sum(i.execution_status == "success" for i in items),
            "failed": sum(i.execution_status == "failed" for i in items),
            "input_tokens": sum(i.input_tokens for i in items), "output_tokens": sum(i.output_tokens for i in items),
            "estimated_cost_usd": round(sum(float(i.estimated_cost) for i in items), 6),
            "average_response_time": _avg([i.response_time for i in items]),
        })
    return {
        "total_requests": len(rows),
        "successful_requests": sum(r.execution_status == "success" for r in rows),
        "failed_requests": sum(r.execution_status == "failed" for r in rows),
        "retry_count": sum(r.attempt > 1 for r in rows),
        "input_tokens": sum(r.input_tokens for r in rows), "output_tokens": sum(r.output_tokens for r in rows),
        "estimated_cost_usd": round(sum(float(r.estimated_cost) for r in rows), 6),
        "average_response_time": _avg([r.response_time for r in rows]),
        "cost_note": "Costs are estimates from a built-in price table, not provider invoices.",
        "by_provider": by_provider,
    }


def performance_stats(db: Session) -> dict:
    usage = db.scalars(select(AIUsage)).all()
    latencies = [u.response_time for u in usage]
    by_provider = defaultdict(list)
    for u in usage:
        by_provider[u.provider].append(u.response_time)

    completed = db.execute(select(WorkflowLog.execution_time).where(WorkflowLog.workflow_step == "workflow_completed")).scalars().all()
    failed = db.scalar(select(func.count()).select_from(WorkflowLog).where(WorkflowLog.workflow_step == "workflow_failed")) or 0
    done = len(completed)
    return {
        "ai_success_rate": _pct(sum(u.execution_status == "success" for u in usage), len(usage)),
        "average_latency_seconds": _avg(latencies), "p95_latency_seconds": _p95(latencies),
        "workflows_completed": done, "workflows_failed": failed,
        "workflow_success_rate": _pct(done, done + failed),
        "average_workflow_seconds": _avg([c for c in completed if c is not None]),
        "latency_by_provider": [{"provider": p, "requests": len(v), "average": _avg(v), "p95": _p95(v)}
                                for p, v in sorted(by_provider.items())],
    }
