"""Workflow orchestrator: runs every pipeline step in order, logs each one, and guarantees that
a failure never loses the original enquiry and a retry never creates duplicate records.

Design notes:
  * Steps compute results IN MEMORY; everything is written in ONE transaction at 'database_update'.
  * Each step writes its own workflow_logs row (status, duration, error) and commits it separately,
    so history survives even when the main transaction is rolled back.
  * analysis / lead score / response have a UNIQUE enquiry_id and are upserted; pending follow-ups are
    replaced — so re-running the workflow is idempotent.
  * An atomic UPDATE ... WHERE ai_status != 'processing' claims the enquiry, preventing concurrent runs.
"""
import logging
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, or_, select, update
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models import AIAnalysis, AIResponse, Enquiry, FollowUp, LeadScore, WorkflowLog
from app.services import (
    classification_service,
    duplicate_service,
    extraction_service,
    followup_service,
    lead_scoring_service,
    priority_service,
    response_service,
    notification_service,
    sentiment_service,
)
from app.utils.helpers import detect_prompt_injection, scrub_secrets

logger = logging.getLogger("leadflow.workflow")
STALE_PROCESSING_MINUTES = 10


def log_step(db: Session, enquiry_id: int, step: str, status: str, message: str | None = None,
             duration: float | None = None) -> None:
    db.add(WorkflowLog(
        enquiry_id=enquiry_id, workflow_step=step, execution_status=status,
        message=scrub_secrets(message)[:1000] if message else None,
        execution_time=round(duration, 4) if duration is not None else None,
    ))
    db.commit()


class _Step:
    """Async context manager: times a step and records success/failure in workflow_logs."""

    def __init__(self, db: Session, enquiry_id: int, name: str):
        self.db, self.enquiry_id, self.name = db, enquiry_id, name
        self.message: str | None = None

    async def __aenter__(self):
        self._t0 = time.perf_counter()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        duration = time.perf_counter() - self._t0
        if exc is None:
            log_step(self.db, self.enquiry_id, self.name, "success", self.message, duration)
        else:
            self.db.rollback()  # discard any half-done writes before logging the failure
            log_step(self.db, self.enquiry_id, self.name, "failed", f"{type(exc).__name__}: {exc}", duration)
        return False  # always propagate


def is_processing(enquiry: Enquiry) -> bool:
    if enquiry.ai_status != "processing":
        return False
    updated = enquiry.updated_at
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - updated < timedelta(minutes=STALE_PROCESSING_MINUTES)


def _claim(db: Session, enquiry_id: int) -> bool:
    stale = datetime.now(timezone.utc) - timedelta(minutes=STALE_PROCESSING_MINUTES)
    result = db.execute(
        update(Enquiry)
        .where(Enquiry.id == enquiry_id, or_(Enquiry.ai_status != "processing", Enquiry.updated_at < stale))
        .values(ai_status="processing", updated_at=datetime.now(timezone.utc))
    )
    db.commit()
    return result.rowcount == 1


def recover_interrupted(db: Session) -> int:
    """On startup: anything left 'processing' was interrupted by a crash/restart — mark failed so it can be retried."""
    ids = db.scalars(select(Enquiry.id).where(Enquiry.ai_status == "processing")).all()
    for eid in ids:
        db.execute(update(Enquiry).where(Enquiry.id == eid).values(ai_status="failed"))
        db.add(WorkflowLog(enquiry_id=eid, workflow_step="workflow_failed", execution_status="failed",
                           message="Processing was interrupted by a server restart; retry available"))
    db.commit()
    return len(ids)


async def process_enquiry(enquiry_id: int) -> None:
    """Entry point used by background tasks and by the admin 'reanalyze' action."""
    db = SessionLocal()
    try:
        await _run(db, enquiry_id)
    except Exception:  # last line of defence: a background task must never crash the server
        logger.exception("unhandled workflow error for enquiry %s", enquiry_id)
    finally:
        db.close()


async def _run(db: Session, enquiry_id: int) -> None:
    if db.get(Enquiry, enquiry_id) is None:
        return
    if not _claim(db, enquiry_id):
        logger.info("enquiry %s is already being processed; skipping", enquiry_id)
        return

    started = time.perf_counter()
    log_step(db, enquiry_id, "workflow_started", "success", "AI processing started")
    try:
        enquiry = db.get(Enquiry, enquiry_id)
        message = enquiry.message

        async with _Step(db, enquiry_id, "duplicate_detection") as st:
            dup = duplicate_service.find_duplicate(db, enquiry)
            enquiry.duplicate_of_id, enquiry.duplicate_reason = (dup if dup else (None, None))
            db.commit()
            st.message = f"Possible duplicate of enquiry #{dup[0]}: {dup[1]}" if dup else "No duplicate found"

        async with _Step(db, enquiry_id, "ai_analysis") as st:
            extraction, meta, notes = await extraction_service.extract(db, enquiry_id, message)
            injection = detect_prompt_injection(message)
            parts = [f"{meta.provider}/{meta.model}, attempt {meta.attempts}"] + notes
            if injection and extraction.urgency is not None:
                # The text contained instructions aimed at the AI, so any urgency the model reports cannot be trusted
                # (it may simply have obeyed "mark this High"). Drop it so it cannot raise priority or score.
                extraction = extraction.model_copy(update={"urgency": None})
                parts.append("Urgency ignored: the message contained instructions aimed at the AI")
            if meta.notes:
                parts.append(f"{len(meta.notes)} earlier failure(s) recovered")
            if meta.skipped:
                parts.append("; ".join(meta.skipped))
            if injection:
                parts.append("Possible prompt-injection text detected; flagged for review")
            st.message = "; ".join(parts)

        async with _Step(db, enquiry_id, "category_classification") as st:
            classification = classification_service.classify(extraction)
            st.message = classification.reason

        async with _Step(db, enquiry_id, "priority_assignment") as st:
            priority = priority_service.assign_priority(extraction)
            st.message = f"{priority.priority}: {priority.reason}"

        async with _Step(db, enquiry_id, "sentiment_intent_analysis") as st:
            si = sentiment_service.analyse(extraction)
            st.message = f"Sentiment {si.sentiment}; intent '{si.intent}'"

        async with _Step(db, enquiry_id, "lead_scoring") as st:
            score = lead_scoring_service.calculate(
                extraction, classification.category, bool(enquiry.email), bool(enquiry.phone), message
            )
            st.message = f"{score.total}/100 ({score.temperature})"

        async with _Step(db, enquiry_id, "missing_information_detection") as st:
            st.message = ", ".join(extraction.missing_information) or "Nothing missing"

        needs_review = classification.needs_manual_review or injection
        async with _Step(db, enquiry_id, "response_generation") as st:
            draft, rmeta = await response_service.generate(
                db, enquiry_id, enquiry.customer_name, message, extraction, classification.category
            )
            st.message = f"{rmeta.provider}/{rmeta.model}, attempt {rmeta.attempts}"

        async with _Step(db, enquiry_id, "followup_suggestions") as st:
            followups = followup_service.suggest(
                enquiry.status, priority.priority, score.temperature, extraction.missing_information, needs_review
            )
            st.message = f"{len(followups)} suggestion(s)"

        async with _Step(db, enquiry_id, "database_update") as st:
            _save_results(db, enquiry_id, extraction, classification, priority, si, score, draft, followups, needs_review)
            st.message = "Analysis, score, response and follow-ups saved"

        # Team email alert. Never raises and never fails the workflow: it is logged as success / skipped / failed.
        t_notify = time.perf_counter()
        n_status, n_message = notification_service.notify_new_enquiry(db, enquiry_id)
        log_step(db, enquiry_id, "email_notification", n_status, n_message, time.perf_counter() - t_notify)

        log_step(db, enquiry_id, "workflow_completed", "success", "Workflow completed", time.perf_counter() - started)
    except Exception as e:
        db.rollback()
        db.execute(update(Enquiry).where(Enquiry.id == enquiry_id).values(ai_status="failed"))
        db.commit()
        log_step(db, enquiry_id, "workflow_failed", "failed",
                 f"Workflow failed; original enquiry preserved. Retry available. ({type(e).__name__})",
                 time.perf_counter() - started)
        logger.warning("workflow failed for enquiry %s: %s", enquiry_id, scrub_secrets(str(e))[:300])


def _save_results(db, enquiry_id, ex, classification, priority, si, score, draft, followups, needs_review) -> None:
    enquiry = db.get(Enquiry, enquiry_id)

    analysis = db.scalar(select(AIAnalysis).where(AIAnalysis.enquiry_id == enquiry_id)) or AIAnalysis(enquiry_id=enquiry_id)
    analysis.service_category = classification.category
    analysis.customer_location = ex.customer_location
    analysis.budget = ex.budget
    analysis.currency = ex.currency
    analysis.urgency = ex.urgency
    analysis.project_timeline = ex.project_timeline
    analysis.project_requirements = ex.requirements
    analysis.missing_information = ex.missing_information
    analysis.summary = ex.summary
    analysis.customer_intent = si.intent
    analysis.sentiment = si.sentiment
    analysis.detected_language = ex.language
    analysis.confidence_score = ex.confidence
    db.add(analysis)

    ls = db.scalar(select(LeadScore).where(LeadScore.enquiry_id == enquiry_id)) or LeadScore(enquiry_id=enquiry_id)
    ls.total_score, ls.budget_score = score.total, score.budget
    ls.requirement_clarity_score, ls.urgency_score = score.clarity, score.urgency
    ls.service_relevance_score, ls.engagement_score = score.relevance, score.engagement
    ls.lead_temperature, ls.scoring_explanation = score.temperature, score.explanation
    db.add(ls)

    resp = db.scalar(select(AIResponse).where(AIResponse.enquiry_id == enquiry_id)) or AIResponse(enquiry_id=enquiry_id)
    resp.generated_response = draft.response  # edited_response (admin's version) is deliberately left untouched
    resp.followup_questions = draft.followup_questions
    db.add(resp)

    # Replace only still-pending suggestions; completed/dismissed ones are history.
    db.execute(delete(FollowUp).where(FollowUp.enquiry_id == enquiry_id, FollowUp.status == "Pending"))
    for f in followups:
        db.add(FollowUp(enquiry_id=enquiry_id, suggested_action=f.action, suggested_date=f.due))

    enquiry.priority, enquiry.priority_reason = priority.priority, priority.reason
    enquiry.needs_manual_review = needs_review
    enquiry.ai_status = "completed"
    db.commit()
