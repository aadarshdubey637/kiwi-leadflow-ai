# Assignment coverage

How this project meets each part of the assignment brief, with where to look. Everything below can be checked in the repository or on the live site.

**Live site:** https://leadflow-ai-iuv5.onrender.com (customer site) · `/admin/login` (admin console) · `/docs` (Swagger API)
**Source code:** https://github.com/aadarshdubey637/kiwi-leadflow-ai
**Demo video:** [`demo/leadflow-walkthrough.webm`](../demo/leadflow-walkthrough.webm)

## Required deliverables (section 8)

| # | Requirement | Where it is |
|---|---|---|
| 1 | Complete source code on GitHub | This repository: `backend/`, `frontend/`, `scripts/`, `docs/`, `Dockerfile`, `render.yaml`. API keys and passwords are not in it (only `.env.example` files) |
| 2 | Working application | Runs locally (README → Quick start) **and** is deployed on Render (Docker image, PostgreSQL): see the live site above |
| 3 | README with installation and setup | [`README.md`](../README.md), plus [`backend/README.md`](../backend/README.md) and [`frontend/README.md`](../frontend/README.md) |
| 4 | Database structure / schema | [`DATABASE.md`](DATABASE.md) (ER diagram, tables, constraints) and [`schema.sql`](schema.sql) (SQLite and PostgreSQL) |
| 5 | Short screen-recorded demonstration (2–3 min) | [`demo/leadflow-walkthrough.webm`](../demo/leadflow-walkthrough.webm): 2 min 42 s screen recording of the real application with on-screen captions (no voice-over). It follows a customer enquiry from submission through AI analysis to the admin console |
| 6 | Explanation of the AI model used | [`AI_MODEL.md`](AI_MODEL.md) |
| 7 | Workflow and system architecture | [`ARCHITECTURE.md`](ARCHITECTURE.md): system diagram, workflow diagram, failure handling, scaling |

## Core requirements (section 3)

| Requirement | Where it is |
|---|---|
| **A. Enquiry input** (name, phone, email, message) | Public form on the customer site and *Add Enquiry* in the admin console; validated in the browser and again on the server |
| **B. AI analysis** (requirements, service, budget, location, urgency, missing information) | `backend/app/services/extraction_service.py`: strict JSON schema, Pydantic validation, grounding checks against invented values |
| **C. Categorisation** (7 categories) | Enforced enum; unsupported categories are rejected; "Other Services" or low confidence is flagged for manual review |
| **D. AI reply** (professional, next steps, follow-up questions, editable) | `response_service.py`; editable on the enquiry page, the original AI draft is always kept |
| **E. Admin dashboard** (6 statistics, category chart, details, analysis, replies, status, search and filter) | Admin console: Overview, Enquiries, Enquiry detail |
| **F. Database** | 9 tables via SQLAlchemy; [`DATABASE.md`](DATABASE.md) |
| **Workflow steps 1–9** | `workflow_service.py`; every step is logged and shown as a timeline (*Workflow History*) |

## Bonus features (section 7): all 10

| # | Feature | Where to see it |
|---|---|---|
| 1 | Duplicate detection | Warning on the enquiry page and a flag in the list (same email, phone or similar text) |
| 2 | AI lead scoring | Score ring with a five-part breakdown and a written explanation; Hot / Warm / Cold |
| 3 | Follow-up reminders | *Follow-ups* page with due dates, overdue badge, mark done / dismiss |
| 4 | WhatsApp | *WhatsApp* button opens a chat with the reply pre-filled |
| 5 | Email notifications | Team alerts and replies to customers over SMTP (needs SMTP settings on the server) |
| 6 | Visual workflow | *Workflow History* timeline per enquiry, with durations and retry attempts |
| 7 | Analytics and reporting | *Analytics* and *AI Monitoring* pages |
| 8 | Automatic assignment | Returning customer keeps their owner, otherwise least-loaded; *Team* page |
| 9 | Export | CSV and Excel from the enquiry list and the analytics page |
| 10 | AI summaries | One-line summary on the detail page and in the list |

## Important instructions (section 10)

| Instruction | How it is met |
|---|---|
| No paid software or subscription | Free Groq and Gemini tiers, SQLite locally, free Render plan, open-source libraries only |
| Free AI tiers or local models | Groq `openai/gpt-oss-120b` primary, Gemini `gemini-2.5-flash` fallback |
| Local demo acceptable | Runs locally; additionally deployed free on Render |
| Keep API keys secure, never upload them | Keys live only in `backend/.env` (git-ignored) and in Render's environment settings. API keys and the SMTP password have never been committed |
| Understand and explain the code | Each design decision is documented with its reason in `docs/` |
| Use sample customer data only | `backend/sample_data/enquiries.json` is fictional; database files are git-ignored |
| Mention third-party libraries | README → *Third-party libraries* |

## Evaluation criteria: evidence

| Criterion (marks) | Evidence |
|---|---|
| **AI integration and implementation (25)** | Two providers behind one interface with automatic fallback; strict JSON schema with Pydantic; retries with a corrective hint; grounding against hallucinated budgets and locations; prompt-injection handling; Hindi and Hinglish tested live; rate-limit-aware scheduler; token, latency and cost tracking |
| **Workflow automation logic (20)** | 16 logged steps, single-transaction save, idempotent retries, atomic job claim, restart recovery, auto-assignment, duplicate detection, follow-ups, email alerts |
| **Backend and API development (15)** | FastAPI, layered routes → services → models, 31 documented endpoints ([`openapi.json`](openapi.json)), JWT auth with roles, rate limiting, consistent error format, 211 automated tests |
| **Problem-solving ability (15)** | Real problems found and fixed by testing against the live APIs: hallucinated values, prompt injection steering priority, free-tier 429s (diagnosed from the provider's message, then a scheduler), a model retired by the provider, Python-version syntax incompatibility (tested on 3.11, 3.12, 3.14), and deployment issues (shared database, proxy IPs, admin bootstrap) |
| **UI/UX and dashboard (10)** | Customer site and admin console, responsive glass-style design, loading / empty / error states, charts from real data |
| **Code quality (5)** | Small single-purpose services, typed Python and TypeScript, comments that explain *why*, lint and type-check clean, no secrets in code |
| **Creativity and additional features (5)** | All 10 bonus features |
| **Project explanation (5)** | `docs/` (architecture, AI model, database, deployment) and the demo video |

## Notes on the live deployment

- Hosted on Render's free plan: the service sleeps after about 15 minutes without traffic, so the first request after a pause can take about a minute.
- The admin credentials are provided with the submission (they are deliberately not stored in the repository).
- Free AI tiers have rate limits; a failed analysis can be retried with one click and the enquiry is never lost.
