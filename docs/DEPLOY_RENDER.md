# Deploying to Render (free)

LeadFlow deploys as **one service on one URL**: the Docker image runs the FastAPI backend *and* serves the built React app, with a free PostgreSQL database next to it. No CORS or API-address settings are needed because the browser and the API share an origin.

This exact setup was tested before writing this guide: the real `Dockerfile` was built, run in production mode against a real PostgreSQL container using Render's `postgres://` URL style, and driven in a browser (customer enquiry → real AI → admin console → exports): 17 of 17 checks passed with no console or HTTP errors.

## Steps

1. **Put the code on GitHub** (Render deploys from a Git repository). The repo contains no secrets.
2. In Render: **New → Blueprint** → choose the repository. Render reads [`render.yaml`](../render.yaml) and proposes a web service `leadflow-ai` and a database `leadflow-db`.
3. Render now asks for the values marked *secret* (they are stored in Render, never in git):

   | Variable | Value |
   |---|---|
   | `ADMIN_EMAIL` | any address for the first admin account |
   | `ADMIN_PASSWORD` | a strong password: this is how you log in at `/admin/login` |
   | `GROQ_API_KEY` | your Groq key (free) |
   | `GEMINI_API_KEY` | your Gemini key (free), the automatic fallback |
   | `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, `NOTIFY_EMAIL` | optional (see the email note below); leave blank to keep email off |

   `JWT_SECRET` is generated automatically and `DATABASE_URL` is wired to the database for you.
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

## Free-tier behaviour you should know about

| Topic | What to expect |
|---|---|
| **Sleeping** | A free web service sleeps after ~15 minutes without traffic and takes roughly a minute to wake on the next visit. Open the URL a minute before a demo. An AI job in progress when it sleeps is marked *failed* on restart and can be retried with one click |
| **Database** | Render's free PostgreSQL is for evaluation: it is deleted after about 30 days unless upgraded. Fine for a submission demo; export your data before then if you need it |
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
- `backend/app/database/connection.py`: connection health checks and recycling for hosted databases; the SQLite-only schema helper is skipped on PostgreSQL.
- `frontend`: production builds call the API on the same origin; local development still uses `VITE_API_BASE_URL`.
