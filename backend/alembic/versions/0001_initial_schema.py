"""Initial schema -- SARO v8.0

Revision ID: 0001
Revises:
Create Date: 2026-03-03
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('tenants',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('subscription_tier', sa.String(32), nullable=False, server_default='trial'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_table('users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('role', sa.String(32), nullable=False, server_default='viewer'),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('tenant_id', 'email', name='uq_users_tenant_email'),
    )
    op.create_table('models',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('model_type', sa.String(64), nullable=False),
        sa.Column('version', sa.String(32), nullable=False, server_default='1.0.0'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_table('regulations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('jurisdiction', sa.String(64), nullable=False),
        sa.Column('effective_date', sa.DateTime(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_table('risk_forecasts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('model_id', sa.String(36), sa.ForeignKey('models.id', ondelete='CASCADE'), nullable=False),
        sa.Column('regulation_id', sa.String(36), sa.ForeignKey('regulations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('probability', sa.Float(), nullable=False),
        sa.Column('confidence_interval', sa.JSON(), nullable=True),
        sa.Column('horizon_days', sa.Integer(), nullable=False, server_default='90'),
        sa.Column('forecast_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_table('audit_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('model_id', sa.String(36), sa.ForeignKey('models.id', ondelete='CASCADE'), nullable=False),
        sa.Column('audit_type', sa.String(64), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(16), nullable=False, server_default='medium'),
        sa.Column('compliance_status', sa.String(32), nullable=False, server_default='review'),
        sa.Column('findings_json', sa.JSON(), nullable=True),
        sa.Column('regulations_json', sa.JSON(), nullable=True),
        sa.Column('audited_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_table('workflows',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('definition_json', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='draft'),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_table('audit_log',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(128), nullable=False),
        sa.Column('resource', sa.String(64), nullable=True),
        sa.Column('resource_id', sa.String(36), nullable=True),
        sa.Column('detail_json', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_audit_log_tenant',    'audit_log',     ['tenant_id'])
    op.create_index('ix_audit_log_created',   'audit_log',     ['created_at'])
    op.create_index('ix_risk_forecasts_model','risk_forecasts', ['model_id'])
    op.create_index('ix_audit_results_model', 'audit_results',  ['model_id'])
    op.create_index('ix_models_tenant',       'models',        ['tenant_id'])
    op.create_index('ix_users_email',         'users',         ['email'])


def downgrade() -> None:
    op.drop_table('audit_log')
    op.drop_table('workflows')
    op.drop_table('audit_results')
    op.drop_table('risk_forecasts')
    op.drop_table('regulations')
    op.drop_table('models')
    op.drop_table('users')
    op.drop_table('tenants')
