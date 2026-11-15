# Deploying to Render (free)

LeadFlow deploys as **one service on one URL**: the Docker image runs the FastAPI backend *and* serves the built React app. It needs a PostgreSQL connection string (see step 3). No CORS or API-address settings are needed because the browser and the API share an origin.

Tested before writing this guide: the real `Dockerfile` was built and run in production mode against a real PostgreSQL container using Render's `postgres://` URL style, and driven in a browser (customer enquiry → real AI → admin console → exports): 17 of 17 checks passed with no console or HTTP errors. The shared-database mode was tested separately (see below).

## Steps

1. **Put the code on GitHub** (Render deploys from a Git repository). The repo contains no secrets.
2. In Render: **New → Blueprint** → choose the repository. Render reads [`render.yaml`](../render.yaml) and proposes one web service, `leadflow-ai`. (The blueprint deliberately does **not** create a database: a Render account may only have one free database, and creating a second fails with *"cannot have more than one active free tier database"*.)
3. Render now asks for the values marked *secret* (they are stored in Render, never in git):

   | Variable | Value |
   |---|---|
   | `DATABASE_URL` | your PostgreSQL connection string: in Render open your existing database → **Connections** → copy the **Internal Database URL** (use the *External* one only if the database is in another region). A free database from Neon works too. For a quick throw-away demo you can type `sqlite:///./leadflow.db` instead (data is lost whenever the free service restarts) |
   | `ADMIN_EMAIL` | optional: an address for the admin account (a placeholder is used if blank) |
   | `ADMIN_PASSWORD` | a strong password: this is how you log in at `/admin/login` |
   | `GROQ_API_KEY` | your Groq key (free) |
   | `GEMINI_API_KEY` | your Gemini key (free), the automatic fallback |
   | `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, `NOTIFY_EMAIL` | optional (see the email note below); leave blank to keep email off |

   `JWT_SECRET` is generated automatically. `DATABASE_SCHEMA=leadflow` is preset (next section).
4. **Apply.** The first build takes a few minutes (it compiles the frontend inside Docker). When it shows *Live*, open the `https://leadflow-ai-….onrender.com` URL:
   - `/` is the customer site
   - `/admin/login` is the admin console (user `admin`, the password you chose)
   - `/docs` is the Swagger API documentation
5. Load demo data against the live site if you want (it uses the public API and your admin login):
   ```bash
   backend\.venv\Scripts\python scripts\seed_demo_data.py --base-url https://leadflow-ai-XXXX.onrender.com
   ```
   (The script reads `ADMIN_USERNAME` / `ADMIN_PASSWORD` from `backend/.env`; set those to your Render values first, or just add enquiries through the site.)

Every `git push` to the connected branch redeploys automatically.

**Changing the admin password:** `ADMIN_PASSWORD` in Render is the source of truth. Edit it under the service's **Environment** tab, save (Render redeploys), and the admin's password is updated on the next start. Use a strong password: the site is public.

## Can't sign in to `/admin/login`?

1. **Is the latest version live?** Open `https://<your-service>.onrender.com/health`. It shows `"commit": "abc1234"`: compare it with the newest commit on GitHub. If it differs, the new build is still running or failed (see the **Events** tab).
2. **`ADMIN_PASSWORD` is the password.** Check it under **Environment**: no quotes around it (they would become part of the password), no leading/trailing spaces. After editing, Render redeploys; the admin's password is re-synced from it on every start. The username is `ADMIN_USERNAME` (preset to `admin`).
3. **Read the logs** (service → **Logs**). At every start LeadFlow prints one line beginning `admin bootstrap:`: *created admin*, *password updated*, *already matches*, or a warning (e.g. *ADMIN_PASSWORD not set*, *wrapped in quotes*). The password itself is never logged.
4. **AI shows "failed" on every enquiry?** Open the enquiry's **Workflow history** for the reason, and the startup log line `AI providers in order: ...` (it says whether each key is set or MISSING). The usual causes: `GROQ_API_KEY` / `GEMINI_API_KEY` blank, or a key pasted into the wrong variable. `AI_PRIMARY_PROVIDER` must be exactly `groq` or `gemini`, and keys go only in the two `*_API_KEY` variables (an invalid provider name is skipped with a warning; the key is never printed).
5. Too many wrong attempts give *"Too many requests"* for a minute (10 per minute per visitor): wait and retry.

## Sharing an existing database safely

`DATABASE_SCHEMA=leadflow` (set in `render.yaml`) makes every LeadFlow connection use its own PostgreSQL schema: the app creates the schema on first start and puts all 9 of its tables there. So you can point it at the free database you already use for another project and **nothing in that project's `public` schema is touched**, even if it has tables with the same names (`enquiries`, `admin_users`).

Verified: against a PostgreSQL where `public.enquiries` and `public.admin_users` already existed with different columns and data, LeadFlow created its tables in `leadflow`, processed a real enquiry with AI, and the other tables were unchanged (same rows, same columns). The value must be a plain identifier (letters, digits, underscore); anything else is rejected at startup.

## Free-tier behaviour you should know about

| Topic | What to expect |
|---|---|
| **Sleeping** | A free web service sleeps after ~15 minutes without traffic and takes roughly a minute to wake on the next visit. Open the URL a minute before a demo. An AI job in progress when it sleeps is marked *failed* on restart and can be retried with one click |
| **Database** | Render allows one free PostgreSQL per account, and it expires after about 30 days unless upgraded. Fine for a submission demo; export your data before then if you need it |
| **Email** | Render has restricted outbound SMTP on free instances. If so, the *Team email alert* step shows **failed** in the Workflow History and everything else carries on normally (an alert can never break processing). Email works fully when you run the app locally; for the hosted site an HTTP email API (e.g. Resend/Brevo) would be the fix |
| **Public site** | Anyone with the link can submit enquiries, and each one uses a little of your free AI quota. The public endpoint is rate limited (20 per minute per IP). Share the link only when you want it used, or suspend the service afterwards |
| **AI free tiers** | Same limits as local: bursts are queued or routed between Groq and Gemini automatically |

## Run the same image locally

```bash
docker build -t leadflow .
docker run -p 10000:10000 -e GROQ_API_KEY=... -e ADMIN_PASSWORD=... -e JWT_SECRET=... leadflow
# -> http://localhost:10000  (uses SQLite inside the container unless you also pass -e DATABASE_URL=postgres://...)
```

## What changed in the code to support this

- `Dockerfile`: two stages (Node builds the React app; a slim Python image runs the API and serves the build). Runs as a non-root user and listens on Render's `$PORT`.
- `backend/app/main.py`: when a frontend build is present it serves `/assets/*` and falls back to `index.html` for client-side routes. Unknown `/api/...` paths still return a JSON 404 and path traversal is blocked (both tested).
- `backend/app/core/config.py`: accepts `postgres://` / `postgresql://` URLs, and uses Render's public URL for links in alert emails.
- `backend/app/database/connection.py`: connection health checks and recycling for hosted databases; optional `DATABASE_SCHEMA` isolation; the SQLite-only schema helper is skipped on PostgreSQL.
- `frontend`: production builds call the API on the same origin; local development still uses `VITE_API_BASE_URL`.
