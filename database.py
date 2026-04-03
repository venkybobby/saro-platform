"""
Database connection and session management.

Uses NullPool so each connection is returned to Neon's pooler immediately —
critical for serverless/edge deployments where persistent connections are not
available.
"""
from __future__ import annotations

import logging
import os

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

_DATABASE_URL: str = os.environ["DATABASE_URL"]

# NullPool: no connection kept alive between requests.
# Suitable for Neon serverless and Koyeb ephemeral instances.
engine = create_engine(
    _DATABASE_URL,
    poolclass=NullPool,
    echo=False,
    connect_args={"connect_timeout": 10},
)

# Emit a debug log on every new connection so we can trace pool behaviour.
@event.listens_for(engine, "connect")
def _on_connect(dbapi_connection, connection_record):  # noqa: ANN001
    logger.debug("New DB connection established")


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


def get_db():
    """
    FastAPI dependency that yields a scoped SQLAlchemy session.

    The session is closed (and connection returned to the pool) after the
    request completes, whether it succeeded or raised an exception.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def health_check() -> bool:
    """Return True if the database is reachable, False otherwise."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("Database health check failed")
        return False
