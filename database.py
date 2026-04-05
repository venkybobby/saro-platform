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

from sqlalchemy import create_engine, event, text
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
