import json
import os

# Must be set before the app (and its cached settings) is imported.
os.environ.setdefault("JWT_SECRET", "test-secret-test-secret-test-secret-0123456789")
os.environ["DATABASE_URL"] = "sqlite://"  # never touch the real leadflow.db from tests
# Environment variables beat .env, so developer settings (real keys, throttling) can't leak into tests.
os.environ["PASSWORD_HASH_ITERATIONS"] = "2000"  # fast hashing for tests that create users
# Email is OFF unless a test turns it on, and a developer's REAL credentials (backend/.env) must never reach a test.
for _name in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM", "NOTIFY_EMAIL"):
    os.environ[_name] = ""
os.environ["AI_MIN_INTERVAL_SECONDS"] = "0"
os.environ["AI_MAX_CONCURRENCY"] = "2"
os.environ["GEMINI_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.core.security import create_access_token, hash_password
from app.database.base import Base
from app.database.connection import get_db
from app.main import app
from app.models import AdminUser
from app.services import ai_service, workflow_service
from app.services.providers.base import LLMProvider, LLMResult

DEFAULT_EXTRACTION = {
    "service_category": "E-commerce Development",
    "budget": 50000,
    "currency": "INR",
    "customer_location": "Indore",
    "urgency": "Medium",
    "project_timeline": None,
    "requirements": ["Product browsing", "Online ordering", "Payment integration"],
    "missing_information": ["Project timeline", "Expected number of products"],
    "intent": "Website development enquiry",
    "sentiment": "Positive",
    "language": "English",
    "summary": "Customer requires an e-commerce website.",
    "confidence": 0.92,
}
DEFAULT_REPLY = {
    "response": "Hello Rahul, thank you for your enquiry about an e-commerce website. "
                "Could you share your timeline and the number of products? We can arrange a short call. "
                "Kiwi Connect Digital Team",
    "followup_questions": ["What is your expected timeline?", "How many products will you list?"],
}

VALID = {
    "customer_name": "Rahul Sharma",
    "email": "rahul@example.com",
    "phone": "+91 98765 43210",
    "message": "I need an e-commerce website for my shop in Indore. Budget 50000 INR.",
}


class FakeProvider(LLMProvider):
    """Scripted stand-in for Gemini/Groq: no network, no cost. Items in `script[task]` are consumed
    first (an Exception is raised, a str is returned raw, a dict is JSON-encoded); then defaults apply."""

    def __init__(self, name: str = "fake"):
        self.name, self.model = name, f"{name}-model"
        self.calls: list[tuple[str, str]] = []
        self.extraction = dict(DEFAULT_EXTRACTION)
        self.reply = dict(DEFAULT_REPLY)
        self.script: dict[str, list] = {"extraction": [], "response": []}

    async def generate(self, system_prompt: str, user_prompt: str) -> LLMResult:
        task = "extraction" if "analysis engine" in system_prompt else "response"
        self.calls.append((task, user_prompt))
        if self.script[task]:
            item = self.script[task].pop(0)
        else:
            item = self.extraction if task == "extraction" else self.reply
        if isinstance(item, Exception):
            raise item
        text = item if isinstance(item, str) else json.dumps(item)
        return LLMResult(text, 100, 50, self.name, self.model)


class _KeepOpen:
    """Lets background workflow code share the test session without closing it."""

    def __init__(self, session):
        self._s = session

    def __getattr__(self, name):
        return getattr(self._s, name)

    def close(self):
        pass


@pytest.fixture(autouse=True)
def _reset_ai_state():
    """Provider cooldowns are process-wide state; never let one test's exhausted quota leak into the next."""
    ai_service._cooldowns.clear()
    yield
    ai_service._cooldowns.clear()


@pytest.fixture()
def db_session():
    """Fresh in-memory SQLite database per test."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    from app import models  # noqa: F401

    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def fake(monkeypatch):
    provider = FakeProvider()
    ai_service.set_provider_chain([provider])
    monkeypatch.setattr(get_settings(), "ai_retry_backoff_seconds", 0.0)
    yield provider
    ai_service.set_provider_chain(None)


@pytest.fixture()
def admin(db_session):
    user = AdminUser(username="admin", email="admin@example.com", role="admin",
                     password_hash=hash_password("secret-pass-1", iterations=1000))
    db_session.add(user)
    db_session.commit()
    return user


def _make_client(db_session, monkeypatch, token: str | None):
    app.dependency_overrides[get_db] = lambda: db_session
    monkeypatch.setattr(workflow_service, "SessionLocal", lambda: _KeepOpen(db_session))
    limiter.reset()
    # No `with` block: skips lifespan so the real DB file is never touched in tests.
    c = TestClient(app)
    if token:
        c.headers["Authorization"] = f"Bearer {token}"
    return c


@pytest.fixture()
def client(db_session, fake, admin, monkeypatch):
    """Authenticated admin client; AI calls go to the FakeProvider."""
    token, _ = create_access_token(admin.username, admin.role)
    yield _make_client(db_session, monkeypatch, token)
    app.dependency_overrides.clear()


@pytest.fixture()
def anon_client(db_session, fake, admin, monkeypatch):
    yield _make_client(db_session, monkeypatch, None)
    app.dependency_overrides.clear()


@pytest.fixture()
def valid_payload():
    return dict(VALID)


@pytest.fixture()
def submit(client, valid_payload):
    """Submit an enquiry (workflow runs synchronously inside TestClient) and return its id."""

    def _submit(**overrides) -> int:
        r = client.post("/api/enquiries", json={**valid_payload, **overrides})
        assert r.status_code == 201, r.text
        return r.json()["data"]["id"]

    return _submit
