"""Central AI gateway.

Responsibilities (and nothing else):
  * build the provider chain (primary, then fallback) from configuration
  * call a provider, parse + validate the JSON reply with Pydantic
  * controlled retries (transient errors and invalid output), then fall back to the next provider
  * record every attempt in ai_usage (tokens, latency, estimated cost, status)

The fallback provider is only called after the primary has been exhausted — never in parallel.
"""
import asyncio
import logging
import time
import weakref
from dataclasses import dataclass, field
from typing import TypeVar

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.models import AIUsage
from app.services.providers.base import (
    LLMProvider,
    LLMResult,
    ProviderError,
    ProviderNotConfigured,
    ProviderRateLimited,
)
from app.services.providers.gemini import GeminiProvider
from app.services.providers.groq import GroqProvider
from app.utils.helpers import scrub_secrets
from app.utils.json_parser import JSONParseError, parse_json_object

logger = logging.getLogger("leadflow.ai")
T = TypeVar("T", bound=BaseModel)

# USD per 1M tokens (input, output). Estimates only — check provider pricing pages for real billing.
PRICING = {
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-2.0-flash": (0.10, 0.40),
    "openai/gpt-oss-120b": (0.15, 0.60),
    "openai/gpt-oss-20b": (0.075, 0.30),
    "llama-3.3-70b-versatile": (0.59, 0.79),
}

_provider_override: list[LLMProvider] | None = None

# provider name -> monotonic time until which it is considered out of quota (set when it reports an exhausted quota,
# e.g. Gemini's daily free limit). Avoids wasting one failing request per enquiry just to rediscover that.
_cooldowns: dict[str, float] = {}
MAX_COOLDOWN_SECONDS = 1800  # re-check at least every 30 minutes

# Global throttle so a burst of enquiries can't exceed the provider's rate limit.
# Semaphores are tied to an event loop, so keep one per running loop.
_throttles: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()
_last_call = 0.0


WINDOW_SECONDS = 60.0
EXPECTED_OUTPUT_TOKENS = 350  # rough size of our JSON answers; only used to reserve room BEFORE a call


def estimate_tokens(system_prompt: str, user_prompt: str) -> int:
    """Cheap, deliberately conservative estimate (about 3.5 characters per token) of what one call will use."""
    return int((len(system_prompt) + len(user_prompt)) / 3.5) + EXPECTED_OUTPUT_TOKENS


class _TokenWindow:
    """Sliding 60-second record of tokens spent on one provider, so we stay under its tokens-per-minute limit."""

    def __init__(self):
        self.events: list[list[float]] = []  # [timestamp, tokens]; mutable so a reservation can be corrected
        self.lock = asyncio.Lock()

    def _prune(self, now: float) -> None:
        self.events = [e for e in self.events if now - e[0] <= WINDOW_SECONDS]

    def wait_needed(self, tpm: int, estimate: int, rpm: int = 0) -> float:
        """Seconds until one more call of `estimate` tokens fits both limits (0 = fits now). Stays at 90% of each limit."""
        now = time.monotonic()
        self._prune(now)
        events = sorted(self.events)

        def fits(evs: list[list[float]]) -> bool:
            tokens_ok = not tpm or sum(e[1] for e in evs) + estimate <= tpm * 0.9
            requests_ok = not rpm or len(evs) + 1 <= max(1, int(rpm * 0.9))
            return tokens_ok and requests_ok

        if not events or fits(events):
            return 0.0
        for i, (ts, _) in enumerate(events):  # find the moment enough old calls have aged out of the window
            if fits(events[i + 1 :]):
                return max(0.0, WINDOW_SECONDS - (now - ts)) + 0.05
        return WINDOW_SECONDS

    async def reserve(self, tpm: int, estimate: int, rpm: int = 0) -> list[float]:
        while True:
            async with self.lock:
                wait = self.wait_needed(tpm, estimate, rpm)
                if wait == 0.0:
                    entry = [time.monotonic(), float(estimate)]
                    self.events.append(entry)
                    return entry
            await asyncio.sleep(min(max(wait, 0.2), 15))


class _Throttle:
    def __init__(self, limit: int):
        self.sem = asyncio.Semaphore(max(1, limit))
        self.gate = asyncio.Lock()
        self.windows: dict[str, _TokenWindow] = {}

    def window(self, provider: str) -> _TokenWindow:
        return self.windows.setdefault(provider, _TokenWindow())


def _throttle() -> _Throttle:
    loop = asyncio.get_running_loop()
    if loop not in _throttles:
        _throttles[loop] = _Throttle(get_settings().ai_max_concurrency)
    return _throttles[loop]


def _tpm_limit(provider: LLMProvider) -> int:
    return int(get_settings().ai_tpm_limits.get(provider.name, 0) or 0)  # 0 = no limit configured


def _rpm_limit(provider: LLMProvider) -> int:
    return int(get_settings().ai_rpm_limits.get(provider.name, 0) or 0)


async def _generate_throttled(provider: LLMProvider, system_prompt: str, prompt: str) -> LLMResult:
    global _last_call
    t = _throttle()
    tpm, rpm = _tpm_limit(provider), _rpm_limit(provider)
    entry = None
    if tpm or rpm:
        entry = await t.window(provider.name).reserve(tpm, estimate_tokens(system_prompt, prompt), rpm)
    try:
        return await _generate_inner(t, provider, system_prompt, prompt, entry)
    except BaseException:
        if entry is not None:
            entry[1] = 0.0  # the call failed before using tokens: give the reservation back
        raise


async def _generate_inner(t: "_Throttle", provider: LLMProvider, system_prompt: str, prompt: str, entry) -> LLMResult:
    global _last_call
    async with t.sem:
        interval = get_settings().ai_min_interval_seconds
        if interval > 0:
            async with t.gate:  # space out call START times
                wait = _last_call + interval - time.monotonic()
                if wait > 0:
                    await asyncio.sleep(wait)
                _last_call = time.monotonic()
        t0 = time.perf_counter()
        try:
            result = await provider.generate(system_prompt, prompt)
        except Exception as exc:
            exc.latency = time.perf_counter() - t0  # type: ignore[attr-defined]
            raise
        result.latency = time.perf_counter() - t0
        if entry is not None:
            entry[1] = float(result.input_tokens + result.output_tokens) or entry[1]  # replace the estimate with reality
        return result


class AIProcessingError(AppError):
    status_code = 502
    code = "ai_processing_failed"


@dataclass
class AICallMeta:
    provider: str
    model: str
    attempts: int
    notes: list[str] = field(default_factory=list)  # failures that were recovered from
    skipped: list[str] = field(default_factory=list)  # providers skipped because they were at their token limit


def set_provider_chain(chain: list[LLMProvider] | None) -> None:
    """Inject providers (used by tests). Pass None to restore configuration-driven providers."""
    global _provider_override
    _provider_override = chain


def _build(name: str) -> LLMProvider:
    s = get_settings()
    if name == "gemini":
        return GeminiProvider(s.gemini_api_key, s.gemini_model, s.ai_timeout_seconds)
    if name == "groq":
        return GroqProvider(s.groq_api_key, s.groq_model, s.ai_timeout_seconds, reasoning_effort=s.groq_reasoning_effort)
    raise ValueError(f"Unknown AI provider '{name}' (supported: gemini, groq)")


def get_provider_chain() -> list[LLMProvider]:
    if _provider_override is not None:
        return _provider_override
    s = get_settings()
    names = [s.ai_primary_provider]
    if s.ai_fallback_provider and s.ai_fallback_provider != s.ai_primary_provider:
        names.append(s.ai_fallback_provider)
    return [_build(n.strip().lower()) for n in names]


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    price_in, price_out = PRICING.get(model, (0.0, 0.0))
    return round((input_tokens * price_in + output_tokens * price_out) / 1_000_000, 6)


def _record_usage(
    db: Session, enquiry_id: int | None, provider: str, model: str, task: str, attempt: int,
    latency: float, result: LLMResult | None, status: str, error: str | None = None,
) -> None:
    try:
        in_t = result.input_tokens if result else 0
        out_t = result.output_tokens if result else 0
        db.add(AIUsage(
            enquiry_id=enquiry_id, provider=provider, model_name=model, task=task, attempt=attempt,
            input_tokens=in_t, output_tokens=out_t,
            response_time=round(latency, 3),
            estimated_cost=estimate_cost(model, in_t, out_t),
            execution_status=status,
            error_message=scrub_secrets(error)[:300] if error else None,
        ))
        db.commit()
    except Exception:  # usage tracking must never break the workflow
        db.rollback()
        logger.exception("failed to record AI usage")


async def run_json_task(
    db: Session, enquiry_id: int | None, task: str, system_prompt: str, user_prompt: str, schema: type[T]
) -> tuple[T, AICallMeta]:
    """Run one LLM task and return a validated Pydantic object, or raise AIProcessingError."""
    s = get_settings()
    failures: list[str] = []
    prompt = user_prompt

    skipped: list[str] = []
    chain = get_provider_chain()
    deferred: list[LLMProvider] = []
    # Round 1 (fast path): skip any provider that is merely BUSY (at its rate limit) while another one is still available.
    # Round 2: if everything else failed, come back to the deferred providers and WAIT for their capacity.
    # A busy provider is not a broken provider, so we never give up on it while it could still serve the request.
    for round_no in (1, 2):
        providers = chain if round_no == 1 else deferred
        if not providers:
            break
        for index, provider in enumerate(providers):
            cooling = _cooldowns.get(provider.name, 0.0) - time.monotonic()
            if cooling > 0 and any(_cooldowns.get(p.name, 0.0) <= time.monotonic() for p in chain if p is not provider):
                skipped.append(f"{provider.name} is out of quota (cooling down ~{cooling / 60:.0f} min)")
                continue  # not deferred: it is out, not busy; another provider can serve this request
            tpm, rpm = _tpm_limit(provider), _rpm_limit(provider)
            if round_no == 1 and (tpm or rpm) and index < len(chain) - 1:
                wait = _throttle().window(provider.name).wait_needed(tpm, estimate_tokens(system_prompt, user_prompt), rpm)
                if wait > s.ai_capacity_skip_seconds:
                    skipped.append(f"{provider.name} at its rate limit (~{wait:.0f}s)")
                    deferred.append(provider)
                    logger.info("provider %s at rate-limit capacity (wait %.0fs); trying the next provider first", provider.name, wait)
                    continue
            for attempt in range(1, s.ai_max_attempts + 1):
                try:
                    result = await _generate_throttled(provider, system_prompt, prompt)
                except ProviderNotConfigured as e:
                    failures.append(str(e))
                    logger.warning("provider %s skipped: %s", provider.name, e)
                    break  # nothing was sent; go straight to the next provider
                except ProviderError as e:
                    msg = scrub_secrets(str(e))
                    _record_usage(db, enquiry_id, provider.name, provider.model, task, attempt, getattr(e, "latency", 0.0), None, "failed", msg)
                    failures.append(f"{provider.name} attempt {attempt}: {msg}")
                    logger.warning("provider %s attempt %s failed: %s", provider.name, attempt, msg)
                    if isinstance(e, ProviderRateLimited) and e.quota_exhausted:
                        _cooldowns[provider.name] = time.monotonic() + min(e.retry_after or MAX_COOLDOWN_SECONDS, MAX_COOLDOWN_SECONDS)
                    if not e.retryable or attempt == s.ai_max_attempts:
                        break
                    delay = s.ai_retry_backoff_seconds * 2 ** (attempt - 1)
                    if isinstance(e, ProviderRateLimited):
                        delay = max(delay, (e.retry_after or 0) + 1, 5 * attempt if s.ai_retry_backoff_seconds else 0)
                    await asyncio.sleep(min(delay, 60))
                    continue

                # The call succeeded; now validate the content. Invalid output is a failed attempt.
                try:
                    parsed = schema.model_validate(parse_json_object(result.text))
                except (JSONParseError, ValidationError) as e:
                    reason = _short_reason(e)
                    _record_usage(db, enquiry_id, provider.name, provider.model, task, attempt, result.latency, result,
                                  "failed", f"invalid output: {reason}")
                    failures.append(f"{provider.name} attempt {attempt}: invalid output ({reason})")
                    # One corrective hint on retry; never echo the model's raw text back.
                    prompt = (
                        f"{user_prompt}\n\nYour previous reply was rejected: {reason}. "
                        "Reply again with ONLY one valid JSON object that follows the required schema exactly."
                    )
                    continue

                _record_usage(db, enquiry_id, provider.name, provider.model, task, attempt, result.latency, result, "success")
                return parsed, AICallMeta(provider.name, provider.model, attempt, failures, skipped)

    raise AIProcessingError("All AI providers failed: " + " | ".join(failures)[:900])


def _short_reason(e: Exception) -> str:
    if isinstance(e, ValidationError):
        parts = [f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()[:4]]
        return "; ".join(parts)
    return str(e)
