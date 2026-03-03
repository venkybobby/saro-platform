"""
SARO v8.0 — Eight SQLAlchemy ORM models.

Tables
------
tenants          Multi-tenant root; subscription tier governs feature flags.
users            Per-tenant user accounts with hashed passwords.
models           AI/ML model registry (name, version, metadata).
regulations      Regulatory documents (EU AI Act, NIST RMF, etc.).
risk_forecasts   Bayesian probability forecasts per model + regulation.
audit_results    Compliance audit runs, findings JSON, score.
workflows        Tenant-defined automation workflows (JSON DSL).
audit_log        Immutable change log — every write action recorded here.
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, JSON, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin


def _uuid() -> str:
    return str(uuid.uuid4())


# ── 1. Tenants ────────────────────────────────────────────────────────────────
class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id                = Column(String(36), primary_key=True, default=_uuid)
    name              = Column(String(255), nullable=False, unique=True)
    subscription_tier = Column(String(32),  nullable=False, default="trial")  # trial|pro|enterprise
    is_active         = Column(Boolean, nullable=False, default=True)
    metadata_json     = Column(JSON, nullable=True)

    users      = relationship("User",         back_populates="tenant", cascade="all, delete-orphan")
    models     = relationship("AIModel",      back_populates="tenant", cascade="all, delete-orphan")
    workflows  = relationship("Workflow",     back_populates="tenant", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog",     back_populates="tenant")


# ── 2. Users ──────────────────────────────────────────────────────────────────
class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("tenant_id", "email"),)

    id              = Column(String(36), primary_key=True, default=_uuid)
    tenant_id       = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    email           = Column(String(255), nullable=False)
    role            = Column(String(32),  nullable=False, default="viewer")  # admin|auditor|viewer
    hashed_password = Column(String(255), nullable=True)   # null = magic-link only
    last_login      = Column(DateTime, nullable=True)
    is_active       = Column(Boolean, nullable=False, default=True)

    tenant      = relationship("Tenant", back_populates="users")
    audit_logs  = relationship("AuditLog", back_populates="user")


# ── 3. AI Model Registry ──────────────────────────────────────────────────────
class AIModel(Base, TimestampMixin):
    __tablename__ = "models"

    id            = Column(String(36), primary_key=True, default=_uuid)
    tenant_id     = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name          = Column(String(255), nullable=False)
    model_type    = Column(String(64),  nullable=False)   # classifier|regressor|llm|…
    version       = Column(String(32),  nullable=False, default="1.0.0")
    description   = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    is_active     = Column(Boolean, nullable=False, default=True)

    tenant         = relationship("Tenant",       back_populates="models")
    risk_forecasts = relationship("RiskForecast", back_populates="model", cascade="all, delete-orphan")
    audit_results  = relationship("AuditResult",  back_populates="model", cascade="all, delete-orphan")


# ── 4. Regulations ────────────────────────────────────────────────────────────
class Regulation(Base, TimestampMixin):
    __tablename__ = "regulations"

    id             = Column(String(36), primary_key=True, default=_uuid)
    name           = Column(String(255), nullable=False, unique=True)
    jurisdiction   = Column(String(64),  nullable=False)   # EU|US|UK|APAC
    effective_date = Column(DateTime, nullable=True)
    content        = Column(Text, nullable=True)
    last_updated   = Column(DateTime, default=datetime.utcnow)

    risk_forecasts = relationship("RiskForecast", back_populates="regulation")


# ── 5. Risk Forecasts ─────────────────────────────────────────────────────────
class RiskForecast(Base, TimestampMixin):
    __tablename__ = "risk_forecasts"

    id                  = Column(String(36), primary_key=True, default=_uuid)
    model_id            = Column(String(36), ForeignKey("models.id",      ondelete="CASCADE"), nullable=False)
    regulation_id       = Column(String(36), ForeignKey("regulations.id", ondelete="SET NULL"), nullable=True)
    probability         = Column(Float, nullable=False)
    confidence_interval = Column(JSON, nullable=True)   # {"lower": 0.1, "upper": 0.9}
    horizon_days        = Column(Integer, nullable=False, default=90)
    forecast_metadata   = Column(JSON, nullable=True)

    model      = relationship("AIModel",    back_populates="risk_forecasts")
    regulation = relationship("Regulation", back_populates="risk_forecasts")


# ── 6. Audit Results ──────────────────────────────────────────────────────────
class AuditResult(Base, TimestampMixin):
    __tablename__ = "audit_results"

    id               = Column(String(36), primary_key=True, default=_uuid)
    model_id         = Column(String(36), ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    audit_type       = Column(String(64),  nullable=False)   # bias|transparency|safety|…
    score            = Column(Float, nullable=False)
    risk_level       = Column(String(16),  nullable=False, default="medium")
    compliance_status= Column(String(32),  nullable=False, default="review")
    findings_json    = Column(JSON, nullable=True)
    regulations_json = Column(JSON, nullable=True)
    audited_at       = Column(DateTime, default=datetime.utcnow)

    model = relationship("AIModel", back_populates="audit_results")


# ── 7. Workflows ──────────────────────────────────────────────────────────────
class Workflow(Base, TimestampMixin):
    __tablename__ = "workflows"

    id              = Column(String(36), primary_key=True, default=_uuid)
    tenant_id       = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name            = Column(String(255), nullable=False)
    definition_json = Column(JSON, nullable=False)   # step DAG
    status          = Column(String(32),  nullable=False, default="draft")  # draft|active|paused|archived
    last_run_at     = Column(DateTime, nullable=True)

    tenant = relationship("Tenant", back_populates="workflows")


# ── 8. Audit Log ──────────────────────────────────────────────────────────────
class AuditLog(Base):
    """Immutable audit trail — no updates, inserts only."""
    __tablename__ = "audit_log"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id   = Column(String(36), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)
    user_id     = Column(String(36), ForeignKey("users.id",   ondelete="SET NULL"), nullable=True)
    action      = Column(String(128), nullable=False)   # CREATE_MODEL, RUN_AUDIT, …
    resource    = Column(String(64),  nullable=True)    # models, audits, …
    resource_id = Column(String(36),  nullable=True)
    detail_json = Column(JSON, nullable=True)
    ip_address  = Column(String(45),  nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="audit_logs")
    user   = relationship("User",   back_populates="audit_logs")
