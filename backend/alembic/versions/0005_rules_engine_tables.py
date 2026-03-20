"""SARO v9.3 — Production rules engine tables

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-20

Creates four persistent rule/incident tables that replace all static in-memory
lists in audit_engine.py.  Every audit run now queries these tables live.

Tables:
- eu_ai_act_rules       EU AI Act articles with risk_level and obligation text
- nist_ai_rmf_controls  All 58 NIST AI RMF 1.0 controls (Govern/Map/Measure/Manage)
- aigp_principles       IAPP AIGP governance principles and subtopics
- ai_incidents          Curated AI incident registry for similar-incident matching
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── EU AI Act rules ──────────────────────────────────────────────────────
    op.create_table(
        'eu_ai_act_rules',
        sa.Column('id',             sa.Integer(),     primary_key=True, autoincrement=True),
        sa.Column('article_number', sa.String(16),    nullable=False),
        sa.Column('title',          sa.String(255),   nullable=False),
        sa.Column('risk_level',     sa.String(32),    nullable=True),   # unacceptable|high|limited|minimal
        sa.Column('description',    sa.Text(),        nullable=True),
        sa.Column('obligation',     sa.Text(),        nullable=True),   # what the system must do
        sa.Column('applies_to',     sa.String(128),   nullable=True),   # providers|deployers|all
        sa.Column('created_at',     sa.DateTime(),    nullable=True),
        sa.Column('updated_at',     sa.DateTime(),    nullable=True),
    )
    op.create_index('ix_eu_ai_act_rules_article', 'eu_ai_act_rules', ['article_number'])

    # ── NIST AI RMF controls ─────────────────────────────────────────────────
    op.create_table(
        'nist_ai_rmf_controls',
        sa.Column('id',              sa.Integer(),     primary_key=True, autoincrement=True),
        sa.Column('control_id',      sa.String(32),    nullable=False, unique=True),  # e.g. GOVERN-1.1
        sa.Column('function',        sa.String(32),    nullable=False),   # Govern|Map|Measure|Manage
        sa.Column('category',        sa.String(64),    nullable=True),
        sa.Column('description',     sa.Text(),        nullable=True),
        sa.Column('created_at',      sa.DateTime(),    nullable=True),
        sa.Column('updated_at',      sa.DateTime(),    nullable=True),
    )
    op.create_index('ix_nist_controls_function',   'nist_ai_rmf_controls', ['function'])
    op.create_index('ix_nist_controls_control_id', 'nist_ai_rmf_controls', ['control_id'])

    # ── AIGP principles ──────────────────────────────────────────────────────
    op.create_table(
        'aigp_principles',
        sa.Column('id',          sa.Integer(),     primary_key=True, autoincrement=True),
        sa.Column('domain',      sa.String(128),   nullable=False),
        sa.Column('subtopic',    sa.String(255),   nullable=True),
        sa.Column('description', sa.Text(),        nullable=True),
        sa.Column('item_id',     sa.String(32),    nullable=True),
        sa.Column('created_at',  sa.DateTime(),    nullable=True),
        sa.Column('updated_at',  sa.DateTime(),    nullable=True),
    )
    op.create_index('ix_aigp_principles_domain', 'aigp_principles', ['domain'])

    # ── AI Incidents ─────────────────────────────────────────────────────────
    op.create_table(
        'ai_incidents',
        sa.Column('id',           sa.Integer(),     primary_key=True, autoincrement=True),
        sa.Column('title',        sa.String(512),   nullable=False),
        sa.Column('date',         sa.String(16),    nullable=True),    # YYYY-MM or YYYY
        sa.Column('harm_type',    sa.String(128),   nullable=True),    # MIT domain
        sa.Column('description',  sa.Text(),        nullable=True),
        sa.Column('severity',     sa.String(16),    nullable=True),    # critical|high|medium|low
        sa.Column('source',       sa.String(255),   nullable=True),
        sa.Column('ai_system',    sa.String(255),   nullable=True),    # name of AI system involved
        sa.Column('region',       sa.String(64),    nullable=True),
        sa.Column('created_at',   sa.DateTime(),    nullable=True),
        sa.Column('updated_at',   sa.DateTime(),    nullable=True),
    )
    op.create_index('ix_ai_incidents_harm_type', 'ai_incidents', ['harm_type'])


def downgrade() -> None:
    op.drop_index('ix_ai_incidents_harm_type',    table_name='ai_incidents')
    op.drop_index('ix_aigp_principles_domain',    table_name='aigp_principles')
    op.drop_index('ix_nist_controls_control_id',  table_name='nist_ai_rmf_controls')
    op.drop_index('ix_nist_controls_function',    table_name='nist_ai_rmf_controls')
    op.drop_index('ix_eu_ai_act_rules_article',   table_name='eu_ai_act_rules')
    op.drop_table('ai_incidents')
    op.drop_table('aigp_principles')
    op.drop_table('nist_ai_rmf_controls')
    op.drop_table('eu_ai_act_rules')
