# Submission checklist

## Required deliverables (assignment section 8)

| # | Requirement | Where it is | Status |
|---|---|---|---|
| 1 | Complete source code on GitHub | This repository (`backend/`, `frontend/`, `scripts/`, `docs/`). Secrets are git-ignored; only `.env.example` files are committed | Ready to publish — you share the link |
| 2 | Working application (local demo) | `README.md` → Quick start. Customer site `http://localhost:5173/`, admin console `/admin`, Swagger `http://localhost:8000/docs` | ✅ Verified |
| 3 | README with installation and setup | [`README.md`](../README.md) (+ `backend/README.md`, `frontend/README.md`) | ✅ |
| 4 | Database structure / schema | [`DATABASE.md`](DATABASE.md) (ER diagram, tables, constraints) and [`schema.sql`](schema.sql) (SQLite + PostgreSQL) | ✅ |
| 5 | Short screen-recorded demonstration (2–3 min) | A silent, automated walkthrough of the real app was also generated at `demo/leadflow-walkthrough.webm` as a reference or fallback | ⚠️ **You record** (your voice and face matter to the reviewers) |
| 6 | Explanation of the AI model used | [`AI_MODEL.md`](AI_MODEL.md) | ✅ |
| 7 | Workflow and system architecture | [`ARCHITECTURE.md`](ARCHITECTURE.md) (diagrams of system and workflow) | ✅ |

## Important instructions (assignment section 10)

| Instruction | How it is met |
|---|---|
| No paid software or subscription | Free Groq and Gemini tiers; SQLite; open-source libraries only |
| Free AI tiers or local models | Groq `gpt-oss-120b` and Gemini 2.5 Flash, free tiers; the app is built around their rate limits |
| Local demo is acceptable, no hosting | Runs locally |
| Keep API keys secure, never upload them | Keys only in `backend/.env` (git-ignored). The history was scanned for key patterns before the first commit |
| Understand and explain the code | Every design choice is documented with its reason in `docs/` |
| Do not copy an existing project | Written for this assignment |
| Use sample customer data only | `backend/sample_data/enquiries.json` is fictional; the database file is git-ignored |
| Mention third-party libraries | README → *Third-party libraries* |

## Evaluation criteria — evidence

| Criterion (marks) | Evidence |
|---|---|
| **AI integration and implementation (25)** | Two providers behind one interface with automatic fallback; strict JSON schema + Pydantic; retries with corrective hint; grounding against hallucinated budgets/locations; prompt-injection handling; Hindi/Hinglish tested live; rate-limit-aware scheduler; token/latency/cost tracking |
| **Workflow automation logic (20)** | 16 logged steps, single-transaction save, idempotent retries, atomic job claim, restart recovery, auto-assignment, duplicate detection, follow-ups, email alerts. Visualised as a timeline |
| **Backend and API development (15)** | FastAPI, layered (routes → services → models), 31 documented endpoints (`openapi.json`), JWT auth + roles, rate limiting, consistent error format, 189 automated tests |
| **Problem-solving ability (15)** | Real problems found and fixed during live testing: hallucinated values, prompt injection steering priority, free-tier 429s (diagnosed from the provider's message → scheduler), model retired by the provider, Python-version syntax incompatibility (tested on 3.11 / 3.12 / 3.14) |
| **UI/UX and dashboard (10)** | Customer site + admin console, glass-style responsive design, loading / empty / error states, charts from real data, mobile layout |
| **Code quality (5)** | Small single-purpose services, typed Python and TypeScript, docstrings explaining *why*, lint and type-check clean, no secrets in code |
| **Creativity and additional features (5)** | All 10 bonus features (see README) |
| **Project explanation (5)** | `docs/` (architecture, AI model, database, deployment) and the demo video |

## Before you submit — your to-do list

1. **Publish the repository** and share the link (see the note below).
2. **Record the demo** (2–3 minutes) showing the flow end to end; upload it (Google Drive / YouTube unlisted) and share the link. Do not commit large video files.
3. **Run the app once on a clean setup** exactly as the README says (new terminal, `pip install`, `npm install`), so you know the instructions work for you.
4. **Add your own API key(s)** to `backend/.env` — never to the repository. If a key was ever pasted into a chat, an email or a screenshot, regenerate it in the provider's console.
5. *(Optional)* Fill the `SMTP_*` block in `backend/.env` to demonstrate real email; otherwise say honestly that email needs SMTP credentials.
6. **Be ready to explain the code** in your own words. Be ready to open `workflow_service.py`, `ai_service.py` and `extraction_service.py` and walk through them.

### Publishing note

The repository has been prepared (`.gitignore` blocks secrets and databases; history is a single clean commit). It has **not** been pushed anywhere: publishing code is your decision (public vs private, repository name, account). The GitHub CLI is installed on this machine and signed in, so pushing is a two-command job once you decide:

```bash
gh repo create <name> --public --source . --remote origin --push
```
