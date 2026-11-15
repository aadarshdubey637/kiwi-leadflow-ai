# LeadFlow AI — Frontend

Admin dashboard for the LeadFlow AI backend. React 19 · Vite · TypeScript · Tailwind CSS 4 · React Router · Axios · TanStack Query · React Hook Form + Zod · Recharts · Lucide.

## Run locally
```
# 1. backend (see ../backend/README.md)
cd backend && .venv\Scripts\activate && uvicorn app.main:app --reload     # http://localhost:8000

# 2. frontend
cd frontend
npm install
copy .env.example .env        # VITE_API_BASE_URL=http://127.0.0.1:8000
npm run dev                   # http://localhost:5173  (use "localhost", not 127.0.0.1 — CORS)
```
Two panels in one app:
- **Customer site** — `http://localhost:5173/` (public, no login): services, how it works, and the enquiry form. Customers only ever see a thank-you with a reference number, never any AI or internal data.
- **Admin console** — `http://localhost:5173/admin` (login required): sign in with the admin created by the backend (`ADMIN_USERNAME` / `ADMIN_PASSWORD` in `backend/.env`). `/login` redirects to `/admin/login`.

Other scripts: `npm run build` (type-check + production build) · `npm run preview` · `npm run lint`.

## Pages
| Route | What it shows |
|---|---|
| `/` | **Customer site**: services (Kiwi Connect Digital wording), how it works, public enquiry form, company contact details |
| `/admin/login` | Username/password form (validated), JWT login, redirects back to the page you wanted |
| `/admin` Overview | 5 live stat cards, enquiry growth (daily/weekly/monthly), Hot/Warm/Cold, category & priority charts, conversion, recent enquiries |
| `/admin/enquiries` | Table with search, category/priority/status/lead/date filters (kept in the URL), pagination, assignee filter, inline status change, AI summary under each name, **CSV and Excel export** |
| `/admin/enquiries/new` | Validated form → saves → live AI result (polls until analysed; retry on failure) |
| `/admin/enquiries/:id` | Original message · AI analysis · lead score ring + breakdown + explanation · priority reason · duplicate / manual-review warnings · editable AI reply · **Email / WhatsApp the customer** · message history · follow-ups · assignee · status · re-analyse |
| `/admin/followups` | Follow-up reminders across all enquiries: overdue / pending / done tabs, per-person filter, mark done / dismiss / reopen, overdue badge in the sidebar |
| `/admin/team` | Team workload, how assignment works, add / pause members (admins only) |
| `/admin/intelligence` | Hot/Warm/Cold, score distribution, categories, high-priority and "Hot leads awaiting contact" lists |
| `/admin/workflows[/:id]` | Step-by-step timeline per enquiry (with retry attempts) + global execution log |
| `/admin/analytics` | Trends with date range, category / priority / lead / status charts, conversion, funnel, pipeline estimate, CSV export |
| `/admin/monitoring` | AI requests, success/failed/retries, tokens, latency (avg/p95), estimated cost, per-provider table |

## Structure
```
src/
  api/          axiosInstance (+ error mapping) and one module per backend area
  auth/         AuthContext, ProtectedRoute, tokenStore
  components/   ui/ (Button, Card, Badges, DataTable, Pagination, states…), layout/, enquiry/, charts/
  hooks/        useApi (all React Query hooks + cache invalidation), useExport
  pages/        one file per route (code-split with React.lazy)
  types/        TypeScript types mirroring the backend schemas
  utils/        formatting helpers, workflow step labels
docs/API_MAPPING.md   endpoint → UI mapping and the documented gaps
```

## Look and feel
Warm paper background with soft sage / sand / dusty-blue washes, frosted-glass panels, a deep-teal brand colour with terracotta and ochre accents, a serif headline face on the public site, a custom logo mark and hand-built SVG artwork (no stock photos, no external image requests). Chart colours are muted and stable (each service category keeps one colour everywhere). Motion is subtle and respects `prefers-reduced-motion`. The `slate` and `brand` colour scales are re-mapped in `src/index.css`, so the whole palette can be changed in one place.

## Design decisions
- **Real data only.** Every number comes from the backend. Where the backend has no data (sentiment aggregate, cross-enquiry follow-ups, sorting) the UI says so — see `docs/API_MAPPING.md`.
- **Auth:** the JWT is kept in `sessionStorage` (cleared when the tab closes). The backend is the authority — route guards are only UX; an expired/invalid token on any call logs the user out cleanly. Logout also clears the React Query cache.
- **Polling, not websockets:** the backend processes AI in the background, so pages poll every 3 s only while an enquiry is `pending`/`processing`.
- **Mutations invalidate every dependent query** (stats, charts, lists, workflow, monitoring), so dashboards never show stale totals after an edit.
- **Filters live in the URL** so views can be bookmarked and survive refresh/back.
- **No secrets in the frontend.** Only `VITE_API_BASE_URL` is configured; AI keys exist only in the backend.

## Verification performed
- `tsc` clean, `oxlint` clean, `npm run build` succeeds.
- Optional features browser-tested (34 checks) against a real local SMTP server: auto-assignment spread, filters, team add / pause, agent role limits, overdue reminders, alert and reply emails delivered, WhatsApp link, Excel + CSV download, mobile.
- Customer panel browser-tested (17 checks): public form validation, thank-you with reference number, **no auth token sent** on public submit, no AI data shown to customers, `/admin/*` blocked without login, enquiry appears in the admin console with source "website", mobile layout.
- Browser-tested (headless Edge) against the real backend: login validation & errors, protected-route redirect, expired token handling, every page, add-enquiry validation, AI-failure UI, CSV download, 404 page, mobile drawer & no horizontal overflow, logout (26 checks).
- Browser-tested with a scripted LLM behind the real backend pipeline (used because the free Gemini daily quota was exhausted): all AI-result screens, detail view, response edit/save/reset, status updates, re-analyse, duplicate & review warnings, Hindi content, filters, charts, exports (53 checks).
- Live AI verified through the real stack with **Groq (`openai/gpt-oss-120b`)**: previously failed enquiries were retried and completed; a new enquiry from the public endpoint was analysed and got a drafted reply.
