# API integration mapping

Derived from the backend's live OpenAPI schema (`/openapi.json`) — nothing here is assumed.
All calls go through `src/api/axiosInstance.ts` (base URL from `VITE_API_BASE_URL`, `Authorization: Bearer <jwt>` attached automatically, errors normalised to `ApiError`).

## Endpoint → frontend usage

| Endpoint | Auth | Frontend module | Used by |
|---|---|---|---|
| `POST /api/auth/login` `{username,password}` | public | `authApi.login` | Login page |
| `GET /api/auth/me` | JWT | `authApi.me` | session check on load, header (name/role) |
| `POST /api/enquiries` | public | `enquiryApi.create` | Add Enquiry (sent with the admin's token too; harmless) |
| `GET /api/enquiries` (`page, page_size, search, status, priority, category, temperature, ai_status, date_from, date_to`) | JWT | `enquiryApi.list` | Enquiries, Overview (recent), AI Intelligence lists, Workflow selector |
| `GET /api/enquiries/export` (same filters) | JWT | `enquiryApi.exportCsv` | Export buttons (fetched as Blob because the endpoint is protected) |
| `GET /api/enquiries/{id}` | JWT | `enquiryApi.get` | Enquiry detail, Add Enquiry live result |
| `PUT /api/enquiries/{id}/status` | JWT | `enquiryApi.updateStatus` | Detail page + inline status dropdown in table |
| `POST /api/enquiries/{id}/reanalyze` | JWT | `enquiryApi.reanalyze` | "Re-analyse" / "Retry analysis" (409 if already processing) |
| `PUT /api/enquiries/{id}/response` | JWT | `enquiryApi.updateResponse` | Response editor |
| `GET /api/dashboard/stats` | JWT | `dashboardApi.stats` | Overview stat cards, Analytics status chart, AI Intelligence |
| `GET /api/dashboard/categories` | JWT | `dashboardApi.categories` | Category charts |
| `GET /api/dashboard/priorities` | JWT | `dashboardApi.priorities` | Priority charts |
| `GET /api/analytics/leads` | JWT | `analyticsApi.leads` | Hot/Warm/Cold, score distribution, average score |
| `GET /api/analytics/conversion` | JWT | `analyticsApi.conversion` | Conversion cards/tables |
| `GET /api/analytics/funnel` | JWT | `analyticsApi.funnel` | Lead funnel |
| `GET /api/analytics/trends` (`period, days`) | JWT | `analyticsApi.trends` | Enquiry growth (Overview + Analytics) |
| `GET /api/analytics/pipeline` | JWT | `analyticsApi.pipeline` | Estimated pipeline value (never described as revenue) |
| `PUT /api/enquiries/{id}/assignee`, `POST .../auto-assign` | JWT | `enquiryApi.assign` / `autoAssign` | Assignee select on the detail page |
| `POST /api/enquiries/{id}/send-email` | JWT | `enquiryApi.sendEmail` | "Email" button (disabled with a reason when SMTP is off) |
| `POST /api/enquiries/{id}/whatsapp` | JWT | `enquiryApi.whatsapp` | "WhatsApp" button (opens the returned wa.me link) |
| `GET /api/enquiries/export?format=csv\|xlsx` | JWT | `enquiryApi.exportFile` | CSV and Excel buttons |
| `GET/POST /api/team`, `PUT /api/team/{id}` | JWT (POST/PUT: admin role) | `teamApi` | Team page, assignee dropdowns and filters |
| `GET /api/followups`, `/summary`, `PUT /api/followups/{id}` | JWT | `followupApi` | Follow-ups page, sidebar badge |
| `GET /api/system/capabilities` | JWT | `systemApi.capabilities` | Enables / disables the Email button |
| `GET /api/workflows/{enquiry_id}` | JWT | `workflowApi.timeline` | Workflow timeline |
| `GET /api/workflows` (`page, page_size, status, step`) | JWT | `workflowApi.list` | "All workflow executions" table |
| `GET /api/monitoring/ai-usage` | JWT | `monitoringApi.aiUsage` | AI Monitoring |
| `GET /api/monitoring/performance` | JWT | `monitoringApi.performance` | AI Monitoring |

Envelope: success `{"success":true,"data":…}` (+ `meta` for lists); error `{"success":false,"error":{"code","message","details"}}`.

## Gaps between the frontend plan and the backend (documented, not worked around)

| Plan asks for | Backend reality | What the UI does |
|---|---|---|
| Login with **email** + password | Login field is **username** | Form uses "Username" |
| **Sortable columns** | List endpoint has no sort parameter (fixed: newest first) | Columns are not sortable |
| **Sentiment distribution** charts (AI Intelligence, Analytics) | Sentiment exists per enquiry only; no aggregate endpoint | Cards say "Not provided by the backend" — no invented numbers |
| ~~Leads requiring follow-up~~ | **Resolved:** `GET /api/followups` now provides the cross-enquiry list | Follow-ups page; AI Intelligence still lists *Hot leads still marked New* |
| **Logout** | No endpoint (stateless JWT) | Token and all cached queries are discarded client-side |
| **Token refresh** | No endpoint; token lifetime is `JWT_EXPIRE_MINUTES` (60) | On any 401 the app clears the session and returns to login with a notice |
| **Suggested next steps** (separate from follow-up questions) | Only `followups[]` (suggested actions with dates) and `followup_questions[]` | "Suggested next steps" = `followups`; "Follow-up questions" = `followup_questions` |
| Dedicated **enquiry status distribution** endpoint | Not needed — `/dashboard/stats` already returns new / in-progress / converted / closed counts | Status chart built from `/dashboard/stats` |

Small backend additions that would close the first gaps (**not made — need approval**):
1. `GET /api/analytics/sentiment` → `[{label,count,percentage}]` from `ai_analysis.sentiment`.
2. `GET /api/followups?status=Pending` (paginated, with enquiry id/name) for a true "needs follow-up" list.
3. `sort_by` / `sort_dir` on `GET /api/enquiries`.

## Two panels
- **Customer site** (`/`) uses only the public `POST /api/enquiries` through a separate Axios instance (`publicApi`) that never attaches an admin token. It displays nothing but a thank-you and the enquiry id.
- **Admin console** (`/admin/*`) uses every other endpoint with the JWT.
- The backend has no public "track my enquiry" endpoint, so customers cannot look up status; that would need a new, token-less lookup endpoint (not added).

## Behaviour notes
- **AI runs in the background.** `POST /api/enquiries` returns `ai_status: "pending"`; the UI polls `GET /api/enquiries/{id}` (and list pages with active rows) every 3 s until the status is `completed` or `failed`.
- **Timestamps** are UTC without a zone suffix (SQLite); `utils/format.ts` treats them explicitly as UTC and shows local time.
- **CORS:** the backend allows `http://localhost:3000` and `http://localhost:5173`. Open the app at `localhost`, not `127.0.0.1`, or add the origin to `CORS_ORIGINS` in the backend `.env`.
- **Error mapping** (`axiosInstance.ts`): network → "Cannot reach the server…", 401 → session-expired (login failures keep the backend's "Invalid username or password"), 422 → first field message, 429 → "Too many requests…", 502 → AI-unavailable notice, 5xx → generic. Raw technical text never reaches the UI.
