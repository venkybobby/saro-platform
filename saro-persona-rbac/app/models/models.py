"""
SARO — Database Models (SQLAlchemy ORM)
Tables: tenants, tenants_config, users, audit_logs, persona_permissions
Aligned with Admin Provisioning + Persona Limitation specs (FR-001 → FR-007).
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey, Text, Index,
    UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import JSON as JSONB  # Use JSON for SQLite compat; swap to JSONB for Postgres prod
from sqlalchemy import String as UUIDString

# Use String(36) for UUID columns — works on both SQLite and Postgres
# In production with Postgres, swap to PG_UUID(as_uuid=True)
UUID = lambda **kwargs: String(36)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


# ---------------------------------------------------------------------------
# Tenants
# ---------------------------------------------------------------------------
class Tenant(Base):
    __tablename__ = "tenants"

    tenant_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    sector = Column(String(100), nullable=False, default="general")
    status = Column(String(50), nullable=False, default="active")  # active | suspended | trial
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    config = relationship("TenantConfig", back_populates="tenant", uselist=False, cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")


class TenantConfig(Base):
    __tablename__ = "tenants_config"

    tenant_id = Column(String(36), ForeignKey("tenants.tenant_id", ondelete="CASCADE"), primary_key=True)
    default_roles = Column(JSONB, nullable=False, default=["forecaster"])
    max_roles_per_user = Column(Integer, nullable=False, default=4)
    stripe_subscription_id = Column(String(255), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    tier = Column(String(50), nullable=False, default="trial")  # trial | starter | pro | enterprise
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    tenant = relationship("Tenant", back_populates="config")


# ---------------------------------------------------------------------------
# Users & Roles
# ---------------------------------------------------------------------------
VALID_ROLES = {"forecaster", "autopsier", "enabler", "evangelist", "admin", "viewer"}


class User(Base):
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    roles = Column(JSONB, nullable=False, default=["forecaster"])
    primary_role = Column(String(50), nullable=False, default="forecaster")
    is_admin = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    tenant = relationship("Tenant", back_populates="users")

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_tenant_email"),
        Index("ix_users_email", "email"),
        Index("ix_users_tenant", "tenant_id"),
        CheckConstraint("1=1", name="ck_max_4_roles"),  # Use jsonb_array_length(roles) <= 4 in Postgres
    )


# ---------------------------------------------------------------------------
# Persona Permissions (View-Level RBAC Matrix)
# ---------------------------------------------------------------------------
class PersonaPermission(Base):
    """
    Static permission matrix: which features/tabs each role can access.
    Seeded on deploy; admin can override per-tenant via tenants_config.
    Matches FR-FOR-01…FR-EVA-03 from persona spec.
    """
    __tablename__ = "persona_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String(50), nullable=False, index=True)
    feature_key = Column(String(100), nullable=False)      # e.g., "regulatory_simulations"
    feature_label = Column(String(200), nullable=False)     # e.g., "Regulatory Simulations"
    access_level = Column(String(20), nullable=False)       # full | read_only | summary | denied
    tab_group = Column(String(100), nullable=False)         # UI tab grouping
    description = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("role", "feature_key", name="uq_role_feature"),
    )


# ---------------------------------------------------------------------------
# Audit Log (NFR-002: audit all role access)
# ---------------------------------------------------------------------------
class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=True)
    tenant_id = Column(String(36), ForeignKey("tenants.tenant_id"), nullable=True)
    action = Column(String(100), nullable=False)            # e.g., "provision_user", "role_switch", "access_denied"
    resource = Column(String(200), nullable=True)           # e.g., "regulatory_simulations"
    details = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
