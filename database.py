"""
Database connection and session management.

Uses NullPool so each connection is returned to Neon's pooler immediately —
critical for serverless/edge deployments where persistent connections are not
available.

Engine is created lazily on first use so that importing this module never
raises a KeyError/RuntimeError when DATABASE_URL is not yet in the environment
(e.g. during Koyeb startup before secrets are injected or during unit tests).
"""
from __future__ import annotations

import functools
import logging
import os

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)


# ── Lazy engine factory ───────────────────────────────────────────────────────

def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "Add it as a Koyeb secret or set it in your .env file."
        )
    return url


@functools.lru_cache(maxsize=1)
def _get_engine():
    """Create (once) and return the SQLAlchemy engine."""
    eng = create_engine(
        _database_url(),
        poolclass=NullPool,
        echo=False,
        connect_args={"connect_timeout": 10},
    )

    @event.listens_for(eng, "connect")
    def _on_connect(dbapi_connection, connection_record):  # noqa: ANN001
        logger.debug("New DB connection established")

    return eng


@functools.lru_cache(maxsize=1)
def _get_session_factory():
    return sessionmaker(autocommit=False, autoflush=False, bind=_get_engine())


# ── Public aliases expected by main.py and models.py ─────────────────────────
# `engine` and `Base` are referenced in main.py as:
#   from database import Base, engine, health_check
# We expose a lazy proxy so the names exist at import time but the real engine
# is only constructed when first accessed.

class _EngineProxy:
    """Thin proxy: attribute access and calls are forwarded to the real engine."""

    def __getattr__(self, name: str):
        return getattr(_get_engine(), name)

    def connect(self, *args, **kwargs):
        return _get_engine().connect(*args, **kwargs)

    def dispose(self, *args, **kwargs):
        return _get_engine().dispose(*args, **kwargs)


engine = _EngineProxy()  # type: ignore[assignment]


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


# ── FastAPI dependency ────────────────────────────────────────────────────────

def get_db():
    """
    FastAPI dependency that yields a scoped SQLAlchemy session.

    The session is closed (and connection returned to the pool) after the
    request completes, whether it succeeded or raised an exception.
    """
    db: Session = _get_session_factory()()
    try:
        yield db
    finally:
        db.close()


# ── Schema helpers ────────────────────────────────────────────────────────────

def create_all_tables() -> None:
    """
    Create all ORM-mapped tables that don't yet exist.

    Passes the real engine directly (not the proxy) to avoid the deprecated
    ``bind=`` keyword argument removed in SQLAlchemy 2.x.
    """
    Base.metadata.create_all(_get_engine())


# Column definitions for idempotent ADD COLUMN migrations.
# Format: (table_name, column_name, postgresql_type_clause)
#
# Why this is necessary:
#   SQLAlchemy's create_all() creates MISSING tables but never issues
#   ALTER TABLE on tables that already exist.  Any column added to an ORM
#   model after the table was first created in the live DB will be absent,
#   causing ProgrammingError on every query that selects it.
#
#   These ALTER TABLE … ADD COLUMN IF NOT EXISTS statements are safe to
#   run on every startup: PostgreSQL ignores them when the column already
#   exists (IF NOT EXISTS) and adds the column silently when it is missing.

_COLUMN_MIGRATIONS: list[tuple[str, str, str]] = [
    # ── audits ────────────────────────────────────────────────────────────────
    # batch_id / dataset_name / sample_count / completed_at were added after
    # the audits table was first created in the Neon DB (create_all only ran
    # with the early minimal schema that had id/tenant_id/user_id/status/created_at).
    ("audits", "batch_id",      "VARCHAR(100)"),
    ("audits", "dataset_name",  "VARCHAR(255)"),
    ("audits", "sample_count",  "INTEGER NOT NULL DEFAULT 0"),
    ("audits", "completed_at",  "TIMESTAMP WITH TIME ZONE"),
    # ── scan_reports ─────────────────────────────────────────────────────────
    # Guard against the same drift on scan_reports just in case.
    ("scan_reports", "mit_coverage_score",  "DOUBLE PRECISION"),
    ("scan_reports", "fixed_delta",         "DOUBLE PRECISION"),
    ("scan_reports", "overall_risk_score",  "DOUBLE PRECISION"),
    ("scan_reports", "confidence_score",    "DOUBLE PRECISION"),
]


def run_schema_migrations() -> None:
    """
    Idempotent column-level schema migrations.

    For each entry in _COLUMN_MIGRATIONS, issue:
        ALTER TABLE "<table>" ADD COLUMN IF NOT EXISTS "<col>" <type>

    Uses SQLAlchemy inspect() to skip columns that already exist so no
    ALTER is sent at all after the first successful migration, keeping
    startup fast.  All DDL runs inside a single transaction; if anything
    fails the whole migration rolls back and the error is re-raised so
    the startup log makes the problem obvious.
    """
    eng = _get_engine()
    inspector = inspect(eng)

    with eng.begin() as conn:
        for table_name, col_name, col_type in _COLUMN_MIGRATIONS:
            if not inspector.has_table(table_name):
                logger.debug(
                    "Schema migration skipped — table %r does not exist yet", table_name
                )
                continue

            existing = {c["name"] for c in inspector.get_columns(table_name)}
            if col_name in existing:
                continue  # already present — nothing to do

            sql = (
                f'ALTER TABLE "{table_name}" '
                f'ADD COLUMN IF NOT EXISTS "{col_name}" {col_type}'
            )
            conn.execute(text(sql))
            logger.info(
                "Schema migration applied: ALTER TABLE %s ADD COLUMN %s %s",
                table_name, col_name, col_type,
            )


# ── Health check ──────────────────────────────────────────────────────────────

def health_check() -> bool:
    """Return True if the database is reachable, False otherwise."""
    try:
        with _get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("Database health check failed")
        return False
