"""SARO v9.0 Enhancements — onboarding_sessions, transactions, user_roles

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-16

Stories:
- #1 Onboarding DB Storage: onboarding_sessions table (Redis→RDS async sync)
- #3 Transactional Data:    transactions table (billing, 6-month GDPR purge)
- #5 Multi-Role Support:    user_roles table (AI auto-assign, max 4 roles)
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── onboarding_sessions ─────────────────────────────────────────────────
    op.create_table('onboarding_sessions',
        sa.Column('id',               sa.String(36),  primary_key=True),
        sa.Column('tenant_id',        sa.String(36),  nullable=False),
        sa.Column('email',            sa.String(255), nullable=False),
        sa.Column('company_name',     sa.String(255), nullable=True),
        sa.Column('sector',           sa.String(64),  nullable=True),
        sa.Column('plan',             sa.String(32),  nullable=False, server_default='trial'),
        sa.Column('persona',          sa.String(32),  nullable=False, server_default='enabler'),
        sa.Column('roles_json',       sa.JSON(),      nullable=True),
        sa.Column('stripe_sub_id',    sa.String(128), nullable=True),
        sa.Column('trial_ends_at',    sa.DateTime(),  nullable=True),
        sa.Column('synced_from_cache',sa.Boolean(),   nullable=False, server_default=sa.text('0')),
        sa.Column('metadata_json',    sa.JSON(),      nullable=True),
        sa.Column('created_at',       sa.DateTime(),  nullable=False),
        sa.Column('updated_at',       sa.DateTime(),  nullable=False),
    )
    op.create_index('ix_onboarding_tenant', 'onboarding_sessions', ['tenant_id'])
    op.create_index('ix_onboarding_email',  'onboarding_sessions', ['email'])

    # ── transactions ────────────────────────────────────────────────────────
    op.create_table('transactions',
        sa.Column('id',               sa.String(36),  primary_key=True),
        sa.Column('tenant_id',        sa.String(36),  nullable=False),
        sa.Column('stripe_charge_id', sa.String(128), nullable=True),
        sa.Column('amount_cents',     sa.Integer(),   nullable=False, server_default='0'),
        sa.Column('currency',         sa.String(8),   nullable=False, server_default='usd'),
        sa.Column('status',           sa.String(32),  nullable=False, server_default='pending'),
        sa.Column('plan',             sa.String(64),  nullable=True),
        sa.Column('description',      sa.Text(),      nullable=True),
        sa.Column('period_start',     sa.DateTime(),  nullable=True),
        sa.Column('period_end',       sa.DateTime(),  nullable=True),
        sa.Column('purge_after',      sa.DateTime(),  nullable=True),
        sa.Column('metadata_json',    sa.JSON(),      nullable=True),
        sa.Column('created_at',       sa.DateTime(),  nullable=False),
        sa.Column('updated_at',       sa.DateTime(),  nullable=False),
    )
    op.create_index('ix_transactions_tenant',  'transactions', ['tenant_id'])
    op.create_index('ix_transactions_purge',   'transactions', ['purge_after'])
    op.create_index('ix_transactions_status',  'transactions', ['status'])

    # ── user_roles ──────────────────────────────────────────────────────────
    op.create_table('user_roles',
        sa.Column('id',             sa.String(36),  primary_key=True),
        sa.Column('user_id',        sa.String(36),  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id',      sa.String(36),  nullable=False),
        sa.Column('role',           sa.String(32),  nullable=False),
        sa.Column('assigned_by',    sa.String(32),  nullable=False, server_default='ai_auto'),
        sa.Column('confidence',     sa.Float(),     nullable=True),
        sa.Column('trigger_action', sa.String(128), nullable=True),
        sa.Column('is_primary',     sa.Boolean(),   nullable=False, server_default=sa.text('0')),
        sa.Column('is_active',      sa.Boolean(),   nullable=False, server_default=sa.text('1')),
        sa.Column('created_at',     sa.DateTime(),  nullable=False),
        sa.Column('updated_at',     sa.DateTime(),  nullable=False),
        sa.UniqueConstraint('user_id', 'role', name='uq_user_roles_user_role'),
    )
    op.create_index('ix_user_roles_tenant', 'user_roles', ['tenant_id'])
    op.create_index('ix_user_roles_user',   'user_roles', ['user_id'])


def downgrade() -> None:
    op.drop_table('user_roles')
    op.drop_table('transactions')
    op.drop_table('onboarding_sessions')
