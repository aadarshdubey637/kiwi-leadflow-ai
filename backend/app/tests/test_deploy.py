"""Deployment support: Render-style database URLs, public URL for email links, and serving the built frontend."""
import importlib

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings


# ---------- database URL normalisation (Render hands out postgres://...) ----------
@pytest.mark.parametrize("given,expected", [
    ("postgres://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
    ("postgresql://u:p@host/db?sslmode=require", "postgresql+psycopg://u:p@host/db?sslmode=require"),
    ("postgresql+psycopg://u:p@host/db", "postgresql+psycopg://u:p@host/db"),  # already explicit: untouched
    ("sqlite:///./leadflow.db", "sqlite:///./leadflow.db"),
])
def test_database_url_is_normalised_for_sqlalchemy(given, expected):
    assert Settings(database_url=given).database_url == expected


def test_render_public_url_is_used_for_email_links(monkeypatch):
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://leadflow-ai.onrender.com")
    assert Settings().frontend_url == "https://leadflow-ai.onrender.com"
    assert Settings(frontend_url="https://custom.example").frontend_url == "https://custom.example"  # explicit setting wins


def test_postgres_engine_options_are_applied_only_for_postgres():
    # pool_pre_ping matters on hosted databases that drop idle connections; SQLite must not get it
    from app.database import connection

    assert connection.engine.dialect.name == "sqlite"
    assert connection.ensure_schema(connection.engine) is not None  # runs on SQLite
    from sqlalchemy import create_engine

    pg = create_engine("postgresql+psycopg://u:p@localhost/db", pool_pre_ping=True)
    assert connection.ensure_schema(pg) == []  # the SQLite-flavoured migration is skipped on PostgreSQL (no connection attempted)


# ---------- serving the built frontend from the API process ----------
@pytest.fixture()
def spa_client(tmp_path, monkeypatch):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html><body>LEADFLOW-SPA</body></html>", encoding="utf-8")
    (tmp_path / "assets" / "app-abc123.js").write_text("console.log('bundle')", encoding="utf-8")
    (tmp_path / "favicon.svg").write_text("<svg/>", encoding="utf-8")
    (tmp_path.parent / "secret.txt").write_text("TOP-SECRET", encoding="utf-8")
    monkeypatch.setenv("STATIC_DIR", str(tmp_path))
    import app.main as main

    reloaded = importlib.reload(main)  # STATIC_DIR is read at import time
    yield TestClient(reloaded.app)
    monkeypatch.delenv("STATIC_DIR")
    importlib.reload(main)  # restore the normal (no static) app for any later test


def test_root_and_client_side_routes_serve_index_html(spa_client):
    for path in ("/", "/admin", "/admin/enquiries/5", "/some/unknown/page"):
        r = spa_client.get(path)
        assert r.status_code == 200 and "LEADFLOW-SPA" in r.text, path  # deep links and refreshes keep working


def test_assets_and_root_files_are_served(spa_client):
    assert "bundle" in spa_client.get("/assets/app-abc123.js").text
    assert spa_client.get("/favicon.svg").text == "<svg/>"


def test_api_health_and_docs_are_not_shadowed_by_the_fallback(spa_client):
    assert spa_client.get("/health").json() == {"success": True, "data": {"status": "ok"}}
    r = spa_client.get("/api/does-not-exist")
    assert r.status_code == 404 and r.json()["success"] is False  # unknown API paths stay JSON 404s, never index.html
    assert spa_client.get("/openapi.json").status_code == 200
    assert "Swagger" in spa_client.get("/docs").text


def test_path_traversal_cannot_read_files_outside_the_static_folder(spa_client):
    for evil in ("/../secret.txt", "/..%2fsecret.txt", "/%2e%2e/secret.txt", "/assets/../../secret.txt"):
        r = spa_client.get(evil)
        assert "TOP-SECRET" not in r.text, evil


def test_without_a_build_the_app_has_no_catch_all(monkeypatch):
    monkeypatch.setenv("STATIC_DIR", "/definitely/not/a/real/folder")
    import app.main as main

    plain = TestClient(importlib.reload(main).app)
    assert plain.get("/").status_code == 404  # local development: Vite serves the frontend, not the API
    monkeypatch.delenv("STATIC_DIR")
    importlib.reload(main)


# ---------- sharing a PostgreSQL database safely: LeadFlow keeps its tables in its own schema ----------
@pytest.mark.parametrize("name", ["leadflow", "_lf", "Lead_Flow_2"])
def test_database_schema_accepts_plain_identifiers(name):
    assert Settings(database_schema=name).database_schema == name


@pytest.mark.parametrize("name", ["x; DROP TABLE y", 'a"b', "1abc", "has space", "a" * 64, "public.x"])
def test_database_schema_rejects_anything_that_is_not_a_plain_identifier(name):
    with pytest.raises(Exception):
        Settings(database_schema=name)  # the value is placed into SQL, so it must never contain anything but an identifier


def test_empty_database_schema_means_none():
    assert Settings(database_schema="").database_schema is None


def test_a_developers_real_email_credentials_never_reach_the_test_environment():
    from app.core.config import get_settings

    s = get_settings()
    assert not s.smtp_password and not s.smtp_username and not s.smtp_host and not s.email_enabled  # blanked by conftest
