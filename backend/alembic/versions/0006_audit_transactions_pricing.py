"""SARO v9.3 — Usage metering + pricing config tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-03-24

Creates:
- audit_transactions  — one row per scan; drives Stripe usage-based billing
- pricing_config      — per-tier pricing managed by Admin (no redeploy needed)

Billing model:
  Free tier    — 50 scans/month · $0
  Pro tier     — 500 scans/month · $99/month base + $0.05/extra scan
  Enterprise   — unlimited · custom pricing
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0006'
down_revision: Union[str, None] = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── audit_transactions ───────────────────────────────────────────────────
    op.create_table(
        'audit_transactions',
        sa.Column('id',               sa.String(36),  primary_key=True),
        sa.Column('tenant_id',        sa.String(36),  nullable=True),
        sa.Column('audit_id',         sa.String(64),  nullable=True),
        sa.Column('model_name',       sa.String(255), nullable=True),
        sa.Column('domain',           sa.String(64),  nullable=True),
        sa.Column('tier',             sa.String(32),  nullable=True, server_default='free'),
        sa.Column('cost_cents',       sa.Integer(),   nullable=False, server_default='0'),
        sa.Column('is_included',      sa.Boolean(),   nullable=False, server_default=sa.true()),
        sa.Column('scan_source',      sa.String(32),  nullable=True, server_default='ui'),
        sa.Column('billing_period',   sa.String(16),  nullable=True),
        sa.Column('created_at',       sa.DateTime(),  nullable=True),
        sa.Column('updated_at',       sa.DateTime(),  nullable=True),
    )
    op.create_index('ix_audit_transactions_tenant_id',     'audit_transactions', ['tenant_id'])
    op.create_index('ix_audit_transactions_audit_id',      'audit_transactions', ['audit_id'])
    op.create_index('ix_audit_transactions_billing_period','audit_transactions', ['billing_period'])

    # ── pricing_config ───────────────────────────────────────────────────────
    op.create_table(
        'pricing_config',
        sa.Column('id',                   sa.Integer(),  primary_key=True, autoincrement=True),
        sa.Column('tier',                 sa.String(32), nullable=False, unique=True),
        sa.Column('monthly_base_cents',   sa.Integer(),  nullable=False, server_default='0'),
        sa.Column('included_scans',       sa.Integer(),  nullable=False, server_default='50'),
        sa.Column('per_extra_scan_cents', sa.Integer(),  nullable=False, server_default='5'),
        sa.Column('annual_discount_pct',  sa.Integer(),  nullable=False, server_default='20'),
        sa.Column('is_active',            sa.Boolean(),  nullable=False, server_default=sa.true()),
        sa.Column('description',          sa.Text(),     nullable=True),
        sa.Column('created_at',           sa.DateTime(), nullable=True),
        sa.Column('updated_at',           sa.DateTime(), nullable=True),
    )
    op.create_index('ix_pricing_config_tier', 'pricing_config', ['tier'])

    # Seed default pricing tiers
    op.execute("""
        INSERT INTO pricing_config (id, tier, monthly_base_cents, included_scans, per_extra_scan_cents, annual_discount_pct, is_active, description)
        VALUES
          (1, 'free',       0,      50,   0, 20, 1, 'Free tier: 50 scans/month. Basic audits, reports, policy chat.'),
          (2, 'pro',        9900,   500,  5, 20, 1, 'Pro: $99/month + $0.05/extra scan. Full audits, API access, 12-month history.'),
          (3, 'enterprise', 99900, -1,    0, 20, 1, 'Enterprise: $999+/month. Unlimited scans, dedicated tenancy, SLA 99.99%.')
    """)


def downgrade() -> None:
    op.drop_index('ix_pricing_config_tier',             table_name='pricing_config')
    op.drop_index('ix_audit_transactions_billing_period',table_name='audit_transactions')
    op.drop_index('ix_audit_transactions_audit_id',     table_name='audit_transactions')
    op.drop_index('ix_audit_transactions_tenant_id',    table_name='audit_transactions')
    op.drop_table('pricing_config')
    op.drop_table('audit_transactions')
