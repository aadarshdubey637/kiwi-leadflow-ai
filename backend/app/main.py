import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
