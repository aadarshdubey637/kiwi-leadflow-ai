from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

_is_sqlite = settings.database_url.startswith("sqlite")
if _is_sqlite:
    _connect_args: dict = {"check_same_thread": False}
elif settings.database_schema:
    # Every connection looks in (and creates tables in) the LeadFlow schema first, never the shared `public` one.
    _connect_args = {"options": f"-csearch_path={settings.database_schema}"}
else:
    _connect_args = {}

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    # Hosted databases drop idle connections (e.g. a free instance waking from sleep): test before use, recycle often.
    **({} if _is_sqlite else {"pool_pre_ping": True, "pool_recycle": 300}),
)

if _is_sqlite:
    # SQLite ignores foreign keys unless asked; PostgreSQL always enforces them.
    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema(eng=None) -> list[str]:
    """Add columns introduced after the first release to an EXISTING database (create_all only creates
    missing tables, never missing columns). Idempotent. Alembic is the right tool for a PostgreSQL move."""
    from sqlalchemy import inspect, text

    eng = eng or engine
    if eng.dialect.name != "sqlite":
        return []  # these ALTERs are SQLite-flavoured; a fresh PostgreSQL database is built complete by create_all (use Alembic later)
    insp = inspect(eng)
    wanted = {
        "enquiries": [
            ("assigned_to_id", "INTEGER REFERENCES admin_users(id) ON DELETE SET NULL"),
            ("assigned_at", "DATETIME"),
        ],
        "admin_users": [("is_active", "BOOLEAN NOT NULL DEFAULT 1")],
    }
    applied: list[str] = []
    with eng.begin() as conn:
        for table, cols in wanted.items():
            if not insp.has_table(table):
                continue
            existing = {c["name"] for c in insp.get_columns(table)}
            for name, ddl in cols:
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
                    applied.append(f"{table}.{name}")
        if insp.has_table("enquiries"):
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_enquiries_assigned_to_id ON enquiries (assigned_to_id)"))
    return applied


def init_db() -> None:
    from app import models  # noqa: F401  (registers tables on Base.metadata)
    from app.database.base import Base

    if settings.database_schema and engine.dialect.name == "postgresql":
        from sqlalchemy import text

        with engine.begin() as conn:  # identifier was validated in config, so interpolating it is safe
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.database_schema}"'))
    Base.metadata.create_all(bind=engine)
    ensure_schema()
