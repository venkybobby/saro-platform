"""
SARO v8.0 — DB Engine & Session Factory
Connects via DATABASE_URL env var (PostgreSQL in prod, SQLite for local dev).
"""
import os, time
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./saro_dev.db")

# Normalise Heroku/Railway postgres:// -> postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

_connect_args: dict = {}
_pool_kwargs:  dict = {}

if DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}
    _pool_kwargs  = {"poolclass": StaticPool}

engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
    pool_recycle=1800,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    **_pool_kwargs,
)

if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA journal_mode=WAL")
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db():
    """FastAPI dependency — yields a scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ping_db() -> dict:
    """Health probe — returns latency_ms and DB version string."""
    t0 = time.perf_counter()
    with engine.connect() as conn:
        if DATABASE_URL.startswith("sqlite"):
            version = "SQLite " + str(conn.execute(text("SELECT sqlite_version()")).scalar())
        else:
            version = str(conn.execute(text("SELECT version()")).scalar()).split("\n")[0]
    return {
        "status": "ok",
        "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        "version": version,
    }
