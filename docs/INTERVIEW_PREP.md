# Interview preparation

The assignment's eight discussion questions, answered from how **this project really works**. Use these as a base and put them in your own words — the interviewers said they want to hear that you *understand* the code, not recite it. Every claim below can be shown in the repo; the file to open is given in brackets.

---

## 1. How does your AI workflow operate?

A submitted enquiry is saved immediately (that commit is separate, so nothing can lose it), assigned to a team member, and the HTTP request returns. A background task then runs the pipeline: duplicate check → **LLM call 1** extracts structured JSON → validation and grounding → category → priority → sentiment → lead score → **LLM call 2** drafts the reply and follow-up questions → follow-up suggestions → *one* database transaction saves everything → optional email alert. Every step writes a row to `workflow_logs`, which the admin sees as a timeline. If anything fails, the enquiry is marked `failed` with the reason and the admin presses *Retry*. [`services/workflow_service.py`, `docs/ARCHITECTURE.md`]

Key idea to say out loud: **the LLM reads language; code makes decisions.** The model produces facts; priority, score and follow-ups are deterministic rules.

## 2. How does your AI extract structured information?

A system prompt defines the task and a strict JSON schema; the provider is asked for JSON mode at temperature 0.1. The reply is parsed and validated with **Pydantic** — the category must be one of seven values, numbers must be in range, lists are cleaned. The prompt also encodes rules that prevent hallucination: budget only if stated, location only if mentioned, urgency only with evidence, "a large budget is not evidence of urgency". On top of that a **grounding check** verifies the budget number actually appears in the message (it understands `50k`, `5 lakh`, `₹1,50,000`, Devanagari digits). [`extraction_service.py`, `schemas/ai_analysis.py`]

## 3. How do you handle incorrect AI responses?

Layers, from cheapest to most expensive:
1. **Tolerant parsing** (strips markdown fences) and **strict validation** (Pydantic).
2. **Retry with a corrective hint** — up to 3 attempts per provider; the model's raw text is never echoed back.
3. **Fallback provider** (Groq ⇄ Gemini) — only used when the primary fails or is busy.
4. **Grounding** — invented budgets/locations are discarded and listed as "missing".
5. **Manual-review flag** — low confidence or "Other Services" flags the enquiry and creates a review task.
6. **Human in the loop** — the admin can edit the reply; the original AI draft is always preserved next to the edit.
7. **Safe failure** — if all providers fail, the enquiry is kept, marked `failed`, and retryable; retries are idempotent (UNIQUE keys + atomic claim), so no duplicate rows.

I can demonstrate this: the test suite covers invalid JSON, unsupported category, provider timeout, rate limit, and a hallucinated budget. [`services/ai_service.py`, `tests/test_ai_analysis.py`]

## 4. How would you handle 1,000 enquiries per day?

That is under one enquiry a minute on average, but traffic comes in bursts and each enquiry costs two LLM calls (about 1,600 tokens measured). Where the current design already helps and what I would change:

- **Already there:** the workflow is idempotent and atomically claimed (safe to run on several workers); the API returns immediately; list endpoints are paginated and indexed; a **rate-limit-aware scheduler** tracks tokens and requests per minute per provider and routes or queues instead of failing. I tested a real burst: Groq's free tier allows 8,000 tokens/min, so 12 simultaneous enquiries (about 20k tokens) can't fit in one minute. Before the scheduler, 21–31 of ~45 Groq calls failed with HTTP 429; after it, **all 12 enquiries completed with 0 failed Groq calls** — even while Gemini's quota happened to be exhausted, because the scheduler queued the excess for Groq instead of giving up (it also routes to Gemini when Gemini has capacity).
- **Change for production:** replace FastAPI background tasks with a **durable queue** (Redis + RQ/Celery, or Postgres `SKIP LOCKED`) and several workers; move SQLite → **PostgreSQL** (the models and `docs/schema.sql` already target it; add Alembic); raise the limits (`AI_TPM_LIMITS`) with a paid tier or a self-hosted model; add alerting on queue depth, failure rate and cost per enquiry.

## 5. How would you reduce AI API costs?

*Already done:* only two calls per enquiry; scoring, priority, follow-ups, duplicates and assignment use plain code instead of the LLM; low reasoning effort and an output-token cap on reasoning models; JSON-only outputs (no chatty text); routing to the free provider with capacity; the prompt tells the model to stay brief.
*Next steps, in order of payoff:*
1. **Merge the two calls into one** (extraction + draft) — roughly halves requests and removes a duplicated system prompt.
2. **Generate the reply lazily** — only when an admin opens the enquiry, since many enquiries are spam or duplicates.
3. **Skip or reuse for near-duplicates** — duplicate detection already finds them; reuse the earlier analysis.
4. **Small model for classification, bigger model only for the reply**; trim the system prompt; use provider prompt-caching where available.
5. **Batch off-peak** for non-urgent enquiries.
I track real numbers to make these decisions: `ai_usage` stores tokens, latency and estimated cost per call. [`/admin/monitoring`]

## 6. How would you integrate this with WhatsApp or a CRM?

The design already has the hooks: every enquiry has a `source` column, there is a `communications` audit table, and the pipeline is triggered by one function, so a new channel only needs an adapter.
- **WhatsApp (inbound):** WhatsApp Business Cloud API → webhook → the same `POST /api/enquiries` with `source="whatsapp"`. **Outbound:** the Cloud API send endpoint with approved templates (replies outside the 24-hour window must be templates); log each message in `communications`. Today I implemented click-to-chat (`wa.me` link with the reply pre-filled) because the Business API needs an approved business account — and I record it as *opened*, not *sent*, because WhatsApp doesn't tell us.
- **CRM (HubSpot / Zoho / Salesforce):** on `workflow_completed`, call an adapter that creates a lead from the extracted fields (name, contact, category, budget, score, summary), using the enquiry id as an idempotency key; inbound, a CRM webhook updates the enquiry status. n8n or Make can orchestrate this through a webhook if no custom code is wanted.

## 7. Which part of the project did you find most challenging? *(answer in your own words — real examples you can use)*

- **Making AI output trustworthy.** The model sometimes invents a budget or location; a prompt alone isn't enough, so I added grounding checks and moved decisions (score, priority) into code.
- **Free-tier rate limits.** I first hit HTTP 429s constantly. Reading the 429 bodies showed Groq's limit is 8,000 tokens/minute; the fix was a scheduler that tracks token and request budgets, routes around a busy provider, queues when both are busy, and puts an exhausted provider on cooldown.
- **Reliability under retries:** making the workflow idempotent (UNIQUE keys, atomic claim, single transaction) so a retry or a double-click can never duplicate data.
- A smaller but real one: a reasoning model spends most of its tokens "thinking"; setting low reasoning effort cut usage a lot.

## 8. What improvements would you make with two more days?

1. A durable job queue and PostgreSQL + Alembic (the scaling path above).
2. Merge the two LLM calls into one and add near-duplicate result reuse (cost).
3. An **evaluation set**: 50–100 labelled enquiries, run on every prompt change, reporting category accuracy and budget/location extraction accuracy — this turns "it seems to work" into a measurable number.
4. Customer-facing status tracking (a signed link) and email/WhatsApp inbound parsing.
5. Role-based permissions beyond admin/agent, an audit log for admin edits, and CRM/WhatsApp Business adapters.
6. Playwright browser tests committed to the repo and run in CI.

---

### Likely follow-up questions

| Question | Short answer |
|---|---|
| *Why FastAPI / SQLite instead of Node / MongoDB?* | Python has the best LLM tooling; FastAPI gives async I/O and Pydantic validation; SQLite needs no setup and the models are Postgres-compatible. The data is relational (enquiry ↔ analysis ↔ score ↔ logs). |
| *Why is priority rule-based rather than asked from the LLM?* | The LLM supplies the evidence (urgency); the rule maps it to a priority and records the reason. It is explainable, reproducible and can't be prompt-injected. |
| *Is the lead score "AI"?* | The AI extracts the facts that feed it; the arithmetic is deterministic and shown to the admin with an explanation. |
| *What if both providers are down?* | The enquiry is saved, marked failed with the reason, and retryable from the UI; nothing is lost. |
| *How do you stop a customer manipulating the AI?* | Delimited untrusted input, injection phrases flagged, schema-bound output, decisions in code. There is a test and a live run for it. |
| *How do you know it works?* | 178 automated tests plus live runs against the real APIs with English, Hindi, Hinglish, vague, duplicate and injection enquiries. |
