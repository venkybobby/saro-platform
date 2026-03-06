"""
SARO Persona-Level RBAC — SQLAlchemy Models
=============================================
Maps to RDS tables: users, tenants_config, user_roles, persona_audit_log.
Integrates with admin provisioning (FR-001) and persona limitation (FR-005).
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Float,
    ForeignKey, Text, Enum as SAEnum, Index, UniqueConstraint,
    JSON, CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, INET
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Tenants
# ---------------------------------------------------------------------------
class Tenant(Base):
    __tablename__ = "tenants_config"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    subscription_tier: Mapped[str] = mapped_column(
        String(50), default="trial", nullable=False
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255))
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255))
    max_users: Mapped[int] = mapped_column(Integer, default=10)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Persona config — tenant-level overrides
    allowed_personas: Mapped[Optional[list]] = mapped_column(
        JSON, default=["forecaster", "enabler", "evangelist", "auditor"],
        comment="Which personas this tenant's subscription unlocks"
    )
    custom_view_overrides: Mapped[Optional[dict]] = mapped_column(
        JSON, default={},
        comment="Tenant-specific view route overrides (e.g., hide certain dashboards)"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    provisioned_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), comment="Admin user ID who provisioned this tenant"
    )

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_tenants_slug", "slug"),
        Index("ix_tenants_active", "is_active"),
    )


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants_config.id", ondelete="CASCADE"),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Persona assignments — up to 4 roles per FR-003
    primary_role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="forecaster"
    )
    roles: Mapped[Optional[list]] = mapped_column(
        JSON, default=["forecaster"],
        comment="Array of persona strings; max 4 per FR-003"
    )

    # Session management
    session_timeout_override: Mapped[Optional[int]] = mapped_column(
        Integer, comment="Per-user timeout override in minutes; null = use persona default"
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(45))

    # Magic link auth
    magic_link_token: Mapped[Optional[str]] = mapped_column(String(512))
    magic_link_expires: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    provisioned_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), comment="Admin user ID who created this user"
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    audit_logs = relationship("PersonaAuditLog", back_populates="user")

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_tenant_email"),
        Index("ix_users_tenant", "tenant_id"),
        Index("ix_users_email", "email"),
        Index("ix_users_primary_role", "primary_role"),
        CheckConstraint(
            "primary_role IN ('forecaster', 'enabler', 'evangelist', 'auditor')",
            name="ck_users_valid_primary_role",
        ),
    )


# ---------------------------------------------------------------------------
# Persona Audit Log — tracks every permission check and access attempt
# ---------------------------------------------------------------------------
class PersonaAuditLog(Base):
    __tablename__ = "persona_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants_config.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="e.g., 'scope_check', 'view_access', 'report_request', 'denied'"
    )
    resource: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="API path or view route or report type"
    )
    scope_required: Mapped[Optional[str]] = mapped_column(String(100))
    scope_granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    user_roles_at_time: Mapped[Optional[list]] = mapped_column(
        JSON, comment="Snapshot of user roles at time of check"
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(512))
    details: Mapped[Optional[dict]] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_user", "user_id"),
        Index("ix_audit_tenant", "tenant_id"),
        Index("ix_audit_timestamp", "timestamp"),
        Index("ix_audit_action", "action"),
        Index("ix_audit_denied", "scope_granted", postgresql_where=Column("scope_granted") == False),
    )


# ---------------------------------------------------------------------------
# Session Cache Table (optional — for distributed session tracking)
# ---------------------------------------------------------------------------
class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants_config.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Effective permissions computed at login — cached for the session
    effective_scopes: Mapped[list] = mapped_column(
        JSON, nullable=False, comment="Merged scopes from all assigned personas"
    )
    effective_views: Mapped[list] = mapped_column(
        JSON, nullable=False, comment="Merged view routes from all assigned personas"
    )
    effective_reports: Mapped[list] = mapped_column(
        JSON, nullable=False, comment="Merged report types from all assigned personas"
    )
    data_sensitivity_ceiling: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Max data sensitivity level (0-3)"
    )
    max_export_rows: Mapped[int] = mapped_column(Integer, nullable=False)

    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(512))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        Index("ix_sessions_user", "user_id"),
        Index("ix_sessions_active", "is_active", "expires_at"),
    )
