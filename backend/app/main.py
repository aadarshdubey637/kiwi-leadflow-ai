import logging
import os
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.database.connection import SessionLocal, init_db
from app.routes import (
    analytics_routes, auth_routes, dashboard_routes, enquiry_routes, followup_routes, monitoring_routes,
    system_routes, team_routes, workflow_routes,
)
from app.services import auth_service, workflow_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()  # create tables on startup (Alembic can replace this when moving to PostgreSQL)
    with SessionLocal() as db:
        auth_service.seed_admin_from_env(db)
        recovered = workflow_service.recover_interrupted(db)
        if recovered:
            logging.getLogger("leadflow").warning("marked %s interrupted enquiries as failed", recovered)
    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        "AI-powered lead management & workflow automation backend.\n\n"
        "Public: `POST /api/enquiries`, `POST /api/auth/login`. Everything else needs a Bearer token "
        "(use the **Authorize** button after logging in)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)
register_exception_handlers(app)
for module in (
    auth_routes, enquiry_routes, dashboard_routes, analytics_routes, workflow_routes, monitoring_routes,
    team_routes, followup_routes, system_routes,
):
    app.include_router(module.router)


@app.get("/health", tags=["System"])
def health():
    return {"success": True, "data": {"status": "ok"}}


# ---------------------------------------------------------------------------------------------------------------
# Optional: serve the built React app from this same server (used by the Docker image / Render, so the whole product
# is ONE service on ONE URL, with no CORS or API-address configuration). Only active when a build exists in
# backend/static (or STATIC_DIR); in local development Vite serves the frontend and this block does nothing.
# ---------------------------------------------------------------------------------------------------------------
STATIC_DIR = Path(os.environ.get("STATIC_DIR") or Path(__file__).resolve().parent.parent / "static").resolve()

if (STATIC_DIR / "index.html").is_file():
    if (STATIC_DIR / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        """Single-page-app fallback: any non-API path serves index.html so deep links and refreshes work."""
        if full_path.startswith(("api/", "docs", "redoc", "openapi.json")):
            raise HTTPException(status_code=404, detail="Not found")  # unknown API paths stay a proper JSON 404
        candidate = (STATIC_DIR / full_path).resolve()
        if full_path and candidate.is_file() and STATIC_DIR in candidate.parents:  # e.g. /favicon.svg; blocks ../ traversal
            return FileResponse(candidate)
        return FileResponse(STATIC_DIR / "index.html", headers={"Cache-Control": "no-cache"})
