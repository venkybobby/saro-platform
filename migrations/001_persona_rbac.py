"""
SARO Persona RBAC — Alembic Migration: Initial persona tables
===============================================================
Run with: alembic upgrade head

This migration creates:
  - tenants_config (updated with persona columns)
  - users (updated with multi-role support)
  - persona_audit_log
  - user_sessions
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = "001_persona_rbac"
down_revision = None  # or link to your last migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- tenants_config: add persona columns if not exists --
    op.add_column(
        "tenants_config",
        sa.Column(
            "allowed_personas",
            sa.JSON(),
            server_default='["forecaster","enabler","evangelist","auditor"]',
            comment="Which personas this tenant subscription unlocks",
        ),
    )
    op.add_column(
        "tenants_config",
        sa.Column(
            "custom_view_overrides",
            sa.JSON(),
            server_default="{}",
            comment="Tenant-specific view route overrides",
        ),
    )

    # -- users: add multi-role columns --
    op.add_column(
        "users",
        sa.Column(
            "roles",
            sa.JSON(),
            server_default='["forecaster"]',
            comment="Array of persona strings; max 4 per FR-003",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "session_timeout_override",
            sa.Integer(),
            nullable=True,
            comment="Per-user timeout override in minutes",
        ),
    )

    # -- persona_audit_log --
    op.create_table(
        "persona_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants_config.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("resource", sa.String(255), nullable=False),
        sa.Column("scope_required", sa.String(100), nullable=True),
        sa.Column("scope_granted", sa.Boolean(), nullable=False),
        sa.Column("user_roles_at_time", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index("ix_audit_user", "persona_audit_log", ["user_id"])
    op.create_index("ix_audit_tenant", "persona_audit_log", ["tenant_id"])
    op.create_index("ix_audit_timestamp", "persona_audit_log", ["timestamp"])
    op.create_index("ix_audit_action", "persona_audit_log", ["action"])

    # -- user_sessions --
    op.create_table(
        "user_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants_config.id", ondelete="CASCADE"), nullable=False),
        sa.Column("effective_scopes", sa.JSON(), nullable=False),
        sa.Column("effective_views", sa.JSON(), nullable=False),
        sa.Column("effective_reports", sa.JSON(), nullable=False),
        sa.Column("data_sensitivity_ceiling", sa.Integer(), nullable=False),
        sa.Column("max_export_rows", sa.Integer(), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("is_active", sa.Boolean(), default=True),
    )
    op.create_index("ix_sessions_user", "user_sessions", ["user_id"])
    op.create_index("ix_sessions_active", "user_sessions", ["is_active", "expires_at"])


def downgrade() -> None:
    op.drop_table("user_sessions")
    op.drop_table("persona_audit_log")
    op.drop_column("users", "roles")
    op.drop_column("users", "session_timeout_override")
    op.drop_column("tenants_config", "allowed_personas")
    op.drop_column("tenants_config", "custom_view_overrides")
