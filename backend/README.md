# LeadFlow AI — Backend

AI-powered lead management & workflow automation backend for **Kiwi Connect Digital**.
FastAPI · SQLAlchemy · SQLite (PostgreSQL-compatible) · Pydantic · Gemini / Groq · JWT · Pytest.

A customer enquiry is saved, de-duplicated, analysed by an LLM (category, budget, location, urgency, sentiment,
language, missing info), prioritised, scored, answered with a draft reply and given follow-up suggestions —
every step logged. Results are exposed through a documented REST API for the (later) admin dashboard.

## Quick start
```
cd backend
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env             # then edit .env (see below)
uvicorn app.main:app --reload
```
- Swagger UI: http://127.0.0.1:8000/docs  (log in via `POST /api/auth/login`, then click **Authorize**)
- ReDoc: http://127.0.0.1:8000/redoc · OpenAPI JSON: `/openapi.json` · Health: `/health`
- Tests: `python -m pytest -q` (no API keys or network needed — the LLM is mocked)

### Configuration (.env)
| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` / `GROQ_API_KEY` | Provider credentials (never logged, never committed). At least one is required for AI analysis |
| `AI_PRIMARY_PROVIDER`, `AI_FALLBACK_PROVIDER` | Switch providers by config. Fallback is called only after the primary fails its retries |
| `AI_MAX_CONCURRENCY`, `AI_MIN_INTERVAL_SECONDS` | Throttle LLM calls across all enquiries. For a free tier of ~10 requests/min use `1` and `6` |
| `JWT_SECRET` | Required strong value when `ENVIRONMENT=production` |
| `ADMIN_USERNAME/EMAIL/PASSWORD` | Seeds the first admin at startup (or run `python -m app.create_admin <username> <email>`) |
| `DATABASE_URL` | `sqlite:///./leadflow.db` now; a `postgresql+psycopg://...` URL later (install a driver) |

Without AI keys the server still works: enquiries are stored, `ai_status` becomes `failed`, and the failure is visible in
the workflow timeline. Add a key and call `POST /api/enquiries/{id}/reanalyze` to process them.

## Architecture
```
app/
  core/       config, security (JWT, password hashing), rate limiting, error handling
  database/   engine/session (SQLite FK enforcement on), declarative base
  models/     8 tables          schemas/  Pydantic request/response + LLM output contract
  routes/     thin HTTP layer   services/ all business logic
    providers/  base interface + Gemini + Groq adapters
  utils/      json_parser, validators, helpers (sanitising, injection detection, secret scrubbing)
  tests/      200 tests
```
Key decisions (good interview talking points):
- **Original enquiry is saved first**, in its own commit, before any AI work — AI failure can never lose it.
- **LLM only extracts facts.** Priority, lead score, temperature, follow-ups and duplicate flags are computed by
  explainable backend rules; scores come with a written breakdown. A customer cannot talk the system into a "Hot" lead.
- **Every LLM reply is validated** with Pydantic (strict 7-category enum, ranges, cleaned lists). Invalid JSON/schema →
  controlled retry (max 3 per provider) → fallback provider → clean failure.
- **Grounding checks:** a budget whose number does not appear in the message (understands `50k`, `5 lakh`, `₹1,50,000`,
  Devanagari digits) or a location absent from a Latin-script message is discarded, so nothing is invented.
  (Location is not checked for non-Latin messages, where the model may legitimately transliterate इंदौर → Indore.)
- **Prompt-injection awareness:** customer text is sanitised, wrapped in `<customer_message>` tags, declared untrusted
  in the system prompt, only the first name is sent for the reply (no email/phone sent to the LLM), suspicious text flags
  the enquiry for manual review, and output can only be what the schema allows.
- **Idempotent workflow:** analysis / score / response rows have a UNIQUE `enquiry_id` and are upserted; pending
  follow-ups are replaced; an atomic `UPDATE … WHERE ai_status != 'processing'` stops concurrent runs; results are saved
  in one transaction. Retrying never duplicates data and keeps an admin's edited response.
- **Rate-limit aware:** a global throttle caps concurrent/spaced LLM calls; the provider's `retryDelay` is honoured; an
  exhausted quota (retry delay > 120 s) skips retries and goes straight to the fallback provider.
- **Passwords:** PBKDF2-HMAC-SHA256, random salt, constant-time compare (stdlib). Login errors are identical for unknown
  user / wrong password. JWT requires `exp`+`sub`; `alg=none` and wrong-secret tokens are rejected.
- Sync SQLAlchemy (FastAPI runs sync endpoints in a thread pool; PostgreSQL-compatible); network calls to LLMs are async.
- Processing runs in a FastAPI background task, so `POST /api/enquiries` returns immediately.

## Optional features (all implemented and tested)
| # | Feature | How it works |
|---|---|---|
| 1 | Duplicate detection | Same email, same phone, or similar text (flagged for review, never merged) |
| 2 | AI lead scoring | LLM extracts facts; a transparent 0-100 rule engine scores them and explains every point |
| 3 | Follow-up reminders | Suggested actions with due dates; `GET /api/followups` (pending / overdue / done), mark Done / Dismissed, sidebar overdue badge |
| 4 | WhatsApp | `POST /api/enquiries/{id}/whatsapp` returns a `wa.me` click-to-chat link with the reply pre-filled (10-digit numbers get `DEFAULT_COUNTRY_CODE`). Logged as **opened**: WhatsApp never tells us if you pressed send, so we do not claim "sent". No API keys needed |
| 5 | Email | Real SMTP. (a) **team alerts** after analysis: always to the assignee, plus `NOTIFY_EMAIL` for High priority / Hot / needs-review (once per enquiry, never repeated on re-analysis); (b) **reply to customer** via `POST /api/enquiries/{id}/send-email`. Without `SMTP_HOST` everything is cleanly skipped / refused with a 409, never faked. All attempts are stored in `communications` |
| 6 | Visual workflow | Per-enquiry timeline (16 steps, attempts, durations, errors) |
| 7 | Analytics & reports | Trends, funnel, conversion, pipeline estimate, lead / category / priority distributions, AI monitoring |
| 8 | Auto-assignment | At submission: returning customer keeps their owner, else fewest open enquiries, ties go round-robin; paused members get nothing. Manual reassignment, `/api/team` with workload; only `admin` role can add / pause members |
| 9 | Export | `GET /api/enquiries/export?format=csv\|xlsx` with the same filters as the list; both neutralise spreadsheet formula injection |
| 10 | AI summaries | One-sentence summary per enquiry, shown on the detail page and under each name in the list, searchable |

New endpoints: `PUT /api/enquiries/{id}/assignee`, `POST /api/enquiries/{id}/auto-assign`, `POST /api/enquiries/{id}/send-email`, `POST /api/enquiries/{id}/whatsapp`, `GET|POST /api/team`, `PUT /api/team/{id}`, `GET /api/followups`, `GET /api/followups/summary`, `PUT /api/followups/{id}`, `GET /api/system/capabilities`. List and export also accept `assignee_id` and `unassigned`.

**Email setup:** fill the `SMTP_*` block in `.env` (see `.env.example`; for Gmail use an app password). Email is tested against a real local SMTP server (`aiosmtpd`), not a mock; a live send to Gmail/your provider needs your credentials and has not been run.

**Existing databases:** startup runs an idempotent migration (`ensure_schema`) that adds the new columns to an existing `leadflow.db` without touching data. Tested on an old-schema database and applied to the real one. Use Alembic when moving to PostgreSQL.

## Workflow (logged in `workflow_logs`)
`enquiry_received → original_data_saved → team_assignment → workflow_started → duplicate_detection → ai_analysis →
category_classification → priority_assignment → sentiment_intent_analysis → lead_scoring →
missing_information_detection → response_generation → followup_suggestions → database_update → email_notification → workflow_completed`
On failure the failing step shows `failed` with the error, followed by `workflow_failed`; `ai_status` = `failed`.
`ai_status` values: `pending | processing | completed | failed`. Each retry appends a new `workflow_started …` run.

## Lead scoring (configurable)
Budget 25 (INR tiers, rough FX table in config) · Requirement clarity 20 · Urgency 25 · Service relevance 20 ·
Engagement 10. **Hot ≥ 80, Warm 50–79, Cold < 50** (`HOT_LEAD_THRESHOLD`, `WARM_LEAD_THRESHOLD`).
Priority: urgency-driven (High/Medium/Low); unknown urgency + well-defined request + stated budget → Medium; budget size alone
never raises priority. `confidence_score` is the model's own indicator, not a calibrated probability.
Estimated pipeline value = sum of stated budgets of open, non-duplicate enquiries per currency; it is **not revenue**.

## API reference
**Auth:** `Authorization: Bearer <access_token>` on everything except `POST /api/enquiries`, `POST /api/auth/login`, `/health`.

**Success:** `{"success": true, "data": …}` · **Lists:** also `"meta": {"page","page_size","total","total_pages"}`
**Error:** `{"success": false, "error": {"code","message","details"}}` — codes: `validation_error` (422),
`invalid_credentials`/`http_error` (401), `not_found` (404), `conflict` (409), `rate_limited` (429), `ai_processing_failed` (502).

| Method | Path | Notes |
|---|---|---|
| POST | /api/auth/login | `{username, password}` → `{access_token, token_type, expires_in}` |
| GET | /api/auth/me | current admin |
| POST | /api/enquiries | **public**; 201; needs `customer_name`, `message`, and `email` or `phone`; AI runs in background |
| GET | /api/enquiries | `page, page_size(≤100), search, status, priority, category, temperature, ai_status, date_from, date_to` |
| GET | /api/enquiries/export | CSV with the same filters (formula-injection safe) |
| GET | /api/enquiries/{id} | enquiry + `analysis`, `lead_score` (breakdown + explanation), `response`, `followups` |
| PUT | /api/enquiries/{id}/status | `New \| In Progress \| Converted \| Closed` |
| POST | /api/enquiries/{id}/reanalyze | 202; 409 if already processing; safe to repeat |
| PUT | /api/enquiries/{id}/response | `{edited_response}`; original `generated_response` preserved; `final_response` = edited or original |
| GET | /api/dashboard/stats | total, new, high-priority, in-progress, converted, closed, needs_manual_review, ai_failed |
| GET | /api/dashboard/categories · /priorities | `[{label,count,percentage}]` (all 7 categories always listed) |
| GET | /api/analytics/leads · /conversion · /funnel · /pipeline | distribution, rates, funnel stages, estimated pipeline |
| GET | /api/analytics/trends | `period=daily\|weekly\|monthly`, `days` (≤366) |
| GET | /api/workflows/{enquiry_id} | chronological timeline (step, status, message, execution_time, created_at) |
| GET | /api/workflows | paginated logs; filters `status`, `step` |
| GET | /api/monitoring/ai-usage | requests, success/failed, retries, tokens, estimated USD cost, per provider/model |
| GET | /api/monitoring/performance | AI success rate, avg/p95 latency, workflow success rate & duration |

Example:
```
POST /api/enquiries
{"customer_name":"Rahul Sharma","email":"rahul@example.com","phone":"+91 98765 43210",
 "message":"I need an e-commerce website for my shop in Indore. Budget 50000 INR."}
→ 201 {"success":true,"data":{"id":1,"status":"New","ai_status":"pending","phone":"+919876543210", …}}

GET /api/enquiries/1   (after processing)
→ data.analysis = {"service_category":"E-commerce Development","budget":50000.0,"currency":"INR",
   "customer_location":"Indore","urgency":null,"missing_information":["Project timeline", …],
   "sentiment":"Neutral","detected_language":"English","confidence_score":0.9, …}
  data.lead_score = {"total_score":59,"lead_temperature":"Warm","budget_score":20, …,"scoring_explanation":"Budget 20/25 (…) …"}
  data.priority = "Medium", data.priority_reason = "No urgency stated, but requirements are well defined …"
```

## Database schema
`enquiries` (original data, status, ai_status, priority + reason, needs_manual_review, duplicate_of_id/reason) ·
`ai_analysis` · `ai_responses` · `lead_scores` (all UNIQUE `enquiry_id`, CASCADE delete) · `workflow_logs` ·
`followups` · `ai_usage` (one row per LLM attempt: provider, model, task, attempt, tokens, latency, est. cost, status;
`enquiry_id` SET NULL so cost history survives) · `admin_users`. Foreign keys, indexes and CHECK constraints on all
enumerations (status, category, priority, temperature…). Tables are created at startup; adopt Alembic when moving to PostgreSQL.

## Sample data
`sample_data/enquiries.json` has 7 enquiries: e-commerce, urgent mobile app, **Hindi** website request, AI chatbot (USD),
marketing, a **duplicate** of #1, and a **prompt-injection** attempt. Load them (PowerShell):
```
Get-Content sample_data/enquiries.json -Raw -Encoding UTF8 | ConvertFrom-Json | ForEach-Object {
  Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/enquiries -ContentType 'application/json; charset=utf-8' `
    -Body ([Text.Encoding]::UTF8.GetBytes(($_ | ConvertTo-Json))) }
```
(Each enquiry uses 2 LLM calls — mind your provider's request limits.)

## Testing
`python -m pytest -q` → 200 tests, no network. Covers: validation (name/email/phone/message), extraction (category, budget,
location, missing info, Hindi), invalid JSON, provider failure/timeout/rate-limit/exhausted quota, unsupported category,
retries, fallback-only-when-needed, concurrency throttle, hallucination guard, scoring/priority/follow-up rules, duplicates
(email/phone/text), full workflow + history, failure + retry without duplicates, DB constraints, dashboard/analytics/funnel/
trends/pipeline, CSV (incl. formula injection), monitoring, auth (hashing, JWT attacks, login uniformity), route protection
(16 endpoints), rate limiting, secret scrubbing.

**Verified live (Gemini `gemini-2.5-flash`):** the 7 sample enquiries were processed by the real API — correct
categories, budgets (incl. `5 lakh` → 500000 and Devanagari digits), locations, urgency, Hindi detection and a fluent Hindi
reply, duplicate flagged, prompt-injection attempt classified *Other Services* and flagged for review.

**Groq model note:** Groq retires models over time; `llama-3.3-70b-versatile` returned `model_not_found` for the project key, so the default is now `openai/gpt-oss-120b` (verified live: JSON mode works, ~1.5 s). List what your key can use with `GET https://api.groq.com/openai/v1/models` and override with `GROQ_MODEL`. Both providers' free tiers rate-limit (HTTP 429); the retry/fallback logic absorbs this.

**Provider limits (important):** Gemini's free tier has per-minute *and* per-day request caps. A burst is handled by
throttling + the provider's `retryDelay`; an exhausted daily quota is **not** retried — the call goes straight to the
fallback provider (set `GROQ_API_KEY`), otherwise the enquiry is marked `failed` and can be retried later with
`POST /api/enquiries/{id}/reanalyze`. Each enquiry uses 2 LLM calls (extraction + reply).

