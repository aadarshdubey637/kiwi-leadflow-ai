# The AI model and how it is used

## Models

| Role | Provider | Model | Why |
|---|---|---|---|
| Primary | **Groq** | `openai/gpt-oss-120b` | Free tier, very fast, supports JSON mode. It is a *reasoning* model, so the app asks for `reasoning_effort: low` — extraction does not need long deliberation and low effort cuts tokens and latency |
| Fallback | **Google Gemini** | `gemini-2.5-flash` | Free tier, strong multilingual (Hindi/Hinglish) quality, JSON output mode |

Both sit behind one `LLMProvider` interface (`backend/app/services/providers/`). Which one is primary is a config value (`AI_PRIMARY_PROVIDER`); model names are config too (`GROQ_MODEL`, `GEMINI_MODEL`). Models get retired — during development `llama-3.3-70b-versatile` was removed from the Groq account, which is exactly why the model is configurable. `GET https://api.groq.com/openai/v1/models` lists what a key can use.

Temperature is `0.1` for both: extraction should be repeatable, not creative.

## Two LLM calls per enquiry

1. **Extraction** → a JSON object with the fields in the table below.
2. **Reply drafting** → `{"response": "...", "followup_questions": [...]}` in the customer's language.

Everything else (priority, lead score, follow-ups, duplicates, assignment) is plain code. That is deliberate: it keeps cost low, results explainable, and prompt injection harmless.

### Extraction output (validated by `schemas/ai_analysis.py`)

| Field | Rule |
|---|---|
| `service_category` | Must be exactly one of the 7 categories (case-insensitive match accepted, anything else rejected) |
| `budget`, `currency` | Only if the customer *stated* one; `50k` / `5 lakh` converted to a full number; never guessed |
| `customer_location` | Only a place the customer mentioned |
| `urgency` | `Low` / `Medium` / `High` **only with evidence** (deadline, "urgent", "no hurry"), otherwise `null`. A large budget is explicitly *not* evidence of urgency |
| `project_timeline`, `requirements[]`, `missing_information[]` | Customer's own words / concrete items / what is needed to scope the work |
| `intent`, `sentiment`, `language`, `summary` | Short phrase · Positive/Neutral/Negative · e.g. "Hindi" · one English sentence |
| `confidence` | The model's own estimate 0–1 — an indicator, **not** a calibrated probability |

## How incorrect AI responses are handled

| Problem | What the system does |
|---|---|
| Not valid JSON / wrapped in markdown | Tolerant parser strips fences; if still invalid → retry with a corrective hint (the model's raw text is never echoed back) |
| Wrong shape, unsupported category, out-of-range number | Pydantic rejects it → retry (max 3 per provider) → next provider → clean failure |
| **Invented budget or location** | *Grounding check:* the budget number must appear in the message (understands `50k`, `5 lakh`, `₹1,50,000`, Devanagari digits); an English message must contain the location. Otherwise the value is discarded and "Budget"/"Customer location" is listed as missing. Non-English messages skip the location check because the model may legitimately transliterate (इंदौर → Indore) |
| Low confidence or "Other Services" | Stored, but `needs_manual_review` is set and a review task is suggested |
| Provider down, timeout, rate limit | Retried with back-off, honouring the provider's `retry-after`; then the fallback provider; the original enquiry is always preserved and the admin can press *Retry* |
| Duplicate / contradictory missing-information items | Normalised and de-duplicated by meaning ("Timeline" already covers "Project timeline") |

## Prompt-injection defence

The customer's text is untrusted. It is (1) sanitised (control characters removed, our delimiter tag neutralised, length capped), (2) wrapped in `<customer_message>` tags, (3) declared in the system prompt to be *data, never instructions*, (4) scanned for known attack phrases (the enquiry is flagged for review), and — most importantly — (5) the model's output can only populate the schema's fields, while score, priority and category-gates are computed by code. The test suite includes "ignore previous instructions…" and a live run confirmed the model classified it as *Other Services* with confidence 0.2.

## Rule engines (no LLM involved)

**Priority** — start from the AI's urgency (High/Medium/Low). If urgency is unknown but the request is well defined (≥ 3 requirements, a stated budget, confidence ≥ 0.7) → Medium; otherwise Low. Budget size alone never raises priority. The reason is stored and shown.

**Lead score (0–100)** — configurable thresholds, transparent breakdown:

| Component | Max | Based on |
|---|---:|---|
| Budget suitability | 25 | Stated budget converted to ₹ (tiers from ₹10k to ₹1 lakh+) |
| Requirement clarity | 20 | Number of requirements, timeline known, little missing |
| Urgency | 25 | High 25 · Medium 15 · Low 5 · unknown 0 |
| Service relevance | 20 | Matches a core service, scaled by AI confidence |
| Engagement | 10 | Email and phone given, message detail, location known |

Hot ≥ 80 · Warm 50–79 · Cold < 50 (`HOT_LEAD_THRESHOLD`, `WARM_LEAD_THRESHOLD`). The stored explanation reads like: *"Budget 20/25 (budget ≈ ₹50,000); Clarity 17/20 …; Total 62/100 → Warm lead."*

**Duplicates** — same email, same phone, or text similarity ≥ 0.85 (character ratio and word-set overlap) against recent enquiries. Flagged, never merged.

## Cost, limits and monitoring

- **Tokens per enquiry:** measured at roughly 1,500–2,000 tokens in total across the two calls (the system prompt is the bulk).
- **Estimated cost:** `ai_usage.estimated_cost` uses a built-in per-model price table; it is an *estimate*, not an invoice. Free tiers cost nothing.
- **Free-tier limits observed:** Groq `gpt-oss-120b` allows 8,000 tokens/minute; Gemini 2.5 Flash roughly 10 requests/minute and a daily cap. The scheduler (`AI_TPM_LIMITS`, `AI_RPM_LIMITS`) keeps each provider under its budget, routes to the other provider when one is busy, queues when both are, and cools down a provider whose quota is exhausted.
- **Monitoring:** `GET /api/monitoring/ai-usage` and `/performance` (and the *AI Monitoring* page) report requests, success/failure, retries, tokens, estimated cost and average / p95 latency per provider. Latency excludes time spent queueing.

## What is sent to the model

Only the enquiry text and, for drafting the reply, the customer's *first name* and the already-extracted facts. Email addresses and phone numbers are never sent. API keys are never logged or stored in error messages.
