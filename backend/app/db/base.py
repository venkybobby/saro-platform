"""
SARO v8.0 — Declarative Base + shared timestamp mixin.
Import Base here so Alembic env.py gets all models in one import.
"""
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """Adds created_at / updated_at to any model."""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# Import all ORM models so Alembic sees them via Base.metadata
from app.db import orm_models  # noqa: F401, E402  (side-effect import)
