# Database structure

SQLite by default (`backend/leadflow.db`, created automatically on first start), through SQLAlchemy. The schema is PostgreSQL-compatible: [`schema.sql`](schema.sql) contains the exact `CREATE TABLE` / `CREATE INDEX` statements for **both** dialects, generated from the models by `scripts/export_docs.py`, so it cannot drift from the code.

## Entity-relationship diagram

```mermaid
erDiagram
    admin_users |o--o{ enquiries : "assigned_to_id"
    enquiries |o--o{ enquiries : "duplicate_of_id"
    enquiries ||--o| ai_analysis : "enquiry_id"
    enquiries ||--o| ai_responses : "enquiry_id"
    enquiries |o--o{ ai_usage : "enquiry_id"
    enquiries ||--o{ communications : "enquiry_id"
    admin_users |o--o{ communications : "sent_by_id"
    enquiries ||--o{ followups : "enquiry_id"
    enquiries ||--o| lead_scores : "enquiry_id"
    enquiries ||--o{ workflow_logs : "enquiry_id"
    admin_users {
        INTEGER id PK
        VARCHAR username UK
        VARCHAR email UK
        VARCHAR password_hash
        VARCHAR role
        BOOLEAN is_active
        DATETIME created_at
    }
    enquiries {
        INTEGER id PK
        VARCHAR customer_name
        VARCHAR phone
        VARCHAR email
        TEXT message
        VARCHAR source
        VARCHAR status
        VARCHAR ai_status
        VARCHAR priority
        TEXT priority_reason
        BOOLEAN needs_manual_review
        INTEGER assigned_to_id FK
        DATETIME assigned_at
        INTEGER duplicate_of_id FK
        VARCHAR duplicate_reason
        DATETIME created_at
        DATETIME updated_at
    }
    ai_analysis {
        INTEGER id PK
        INTEGER enquiry_id FK UK
        VARCHAR service_category
        VARCHAR customer_location
        NUMERIC budget
        VARCHAR currency
        VARCHAR urgency
        VARCHAR project_timeline
        JSON project_requirements
        JSON missing_information
        TEXT summary
        VARCHAR customer_intent
        VARCHAR sentiment
        VARCHAR detected_language
        FLOAT confidence_score
        DATETIME created_at
    }
    ai_responses {
        INTEGER id PK
        INTEGER enquiry_id FK UK
        TEXT generated_response
        TEXT edited_response
        JSON followup_questions
        DATETIME created_at
        DATETIME updated_at
    }
    lead_scores {
        INTEGER id PK
        INTEGER enquiry_id FK UK
        INTEGER total_score
        INTEGER budget_score
        INTEGER requirement_clarity_score
        INTEGER urgency_score
        INTEGER service_relevance_score
        INTEGER engagement_score
        VARCHAR lead_temperature
        TEXT scoring_explanation
        DATETIME created_at
    }
    followups {
        INTEGER id PK
        INTEGER enquiry_id FK
        TEXT suggested_action
        DATETIME suggested_date
        VARCHAR status
        DATETIME created_at
    }
    workflow_logs {
        INTEGER id PK
        INTEGER enquiry_id FK
        VARCHAR workflow_step
        VARCHAR execution_status
        TEXT message
        FLOAT execution_time
        DATETIME created_at
    }
    ai_usage {
        INTEGER id PK
        INTEGER enquiry_id FK
        VARCHAR provider
        VARCHAR model_name
        VARCHAR task
        INTEGER attempt
        INTEGER input_tokens
        INTEGER output_tokens
        FLOAT response_time
        NUMERIC estimated_cost
        VARCHAR execution_status
        VARCHAR error_message
        DATETIME created_at
    }
    communications {
        INTEGER id PK
        INTEGER enquiry_id FK
        VARCHAR channel
        VARCHAR kind
        VARCHAR recipient
        VARCHAR subject
        TEXT body
        VARCHAR status
        VARCHAR error
        INTEGER sent_by_id FK
        DATETIME created_at
    }
```

`PK` primary key · `FK` foreign key · `UK` unique. A UNIQUE `enquiry_id` is what makes `ai_analysis`, `ai_responses` and `lead_scores` strictly one-per-enquiry, and what lets a retry *update* a row instead of creating a duplicate.

## Tables

| Table | Purpose | Assignment requirement |
|---|---|---|
| **`enquiries`** | The original customer submission (never modified) plus its status, AI processing state (`ai_status`), priority and the reason for it, manual-review flag, assignee and duplicate link | "Save all customer enquiries", "Store priority", "Maintain enquiry status" |
| **`ai_analysis`** | What the AI extracted: category, location, budget + currency, urgency, timeline, requirements, missing information, summary, intent, sentiment, language, confidence | "Store AI-generated analysis", "Store categories" |
| **`ai_responses`** | The AI-drafted reply (`generated_response`, never overwritten) and the admin's edit (`edited_response`), plus the follow-up questions | "Allow the administrator to review and edit the response" |
| **`lead_scores`** | The 0–100 score, its five components, Hot/Warm/Cold, and a plain-English explanation | Bonus: lead scoring |
| **`followups`** | Suggested next actions with due dates and a Pending / Done / Dismissed state | Bonus: follow-up reminders |
| **`workflow_logs`** | One row per workflow step: status, duration, message / error | Workflow visibility, retry diagnostics |
| **`ai_usage`** | One row per LLM call attempt: provider, model, task, attempt number, tokens, latency, estimated cost, status, error | AI monitoring, cost tracking |
| **`communications`** | Audit trail of every email / WhatsApp action (including failures and team alerts) | Bonus: email, WhatsApp |
| **`admin_users`** | Admin and agent accounts (password stored only as a salted hash), role, active flag | Authentication, team assignment |

### Value sets enforced by database CHECK constraints

| Column | Allowed values |
|---|---|
| `enquiries.status` | `New`, `In Progress`, `Converted`, `Closed` |
| `enquiries.ai_status` | `pending`, `processing`, `completed`, `failed` |
| `enquiries.priority` | `Low`, `Medium`, `High` (or NULL until analysed) |
| `ai_analysis.service_category` | Website Development · Mobile Application Development · AI Software Development · Digital Marketing · E-commerce Development · Custom Software Development · Other Services |
| `lead_scores.lead_temperature` | `Hot`, `Warm`, `Cold`; `total_score` between 0 and 100 |
| `workflow_logs.execution_status` | `started`, `success`, `failed`, `skipped` |

### Integrity rules

- Deleting an enquiry cascades to its analysis, reply, score, follow-ups, workflow logs and communications.
- Deleting a team member sets `assigned_to_id` / `sent_by_id` to NULL (history is kept).
- `ai_usage.enquiry_id` is `SET NULL` on delete, so cost history survives.
- SQLite foreign keys are switched on for every connection (SQLite ignores them by default).
- Indexes on the columns the dashboard filters by: status + created date, priority, email, phone, category, lead temperature, assignee.

## Migrations

`create_all` creates missing *tables* on start-up, and `ensure_schema()` (in `backend/app/database/connection.py`) adds columns that were introduced later to an existing database. It is idempotent and tested against an old-schema file. When moving to PostgreSQL, adopt Alembic.

## Inspecting the data

```bash
sqlite3 backend/leadflow.db ".tables"
sqlite3 backend/leadflow.db "select id, customer_name, status, priority from enquiries order by id desc limit 5;"
```

Or use any SQLite viewer on `backend/leadflow.db`. The file contains whatever you typed in, so it is git-ignored: **sample data only, never real customer information.**
