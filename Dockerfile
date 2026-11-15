# LeadFlow AI: ONE image that serves the API and the React app together (used by Render; also runs anywhere Docker runs).
#   docker build -t leadflow .
#   docker run -p 10000:10000 -e GROQ_API_KEY=... -e ADMIN_PASSWORD=... -e JWT_SECRET=... leadflow     -> http://localhost:10000

# ---- stage 1: build the React app (Node is only needed here, so it is not in the final image) ----
FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# A production build calls the API on its own origin (no VITE_API_BASE_URL needed).
RUN npm run build

# ---- stage 2: the FastAPI backend, which also serves the built frontend from ./static ----
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=web /web/dist ./static
# never run the web server as root
RUN useradd --create-home --uid 10001 app && chown -R app /app
USER app
EXPOSE 10000
# Render injects $PORT; default 10000 matches Render's convention
# --proxy-headers: behind Render's load balancer, take the real client IP from X-Forwarded-For (needed for per-IP rate limits)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --proxy-headers --forwarded-allow-ips='*'"]
