"""SARO v9.2 — Persistent MIT AI Risk Repository table

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-19

Changes:
- CREATE TABLE mit_risks — stores the full 1,612+ risk entries from the MIT
  AI Risk Repository (airisks.mit.edu). Populated once by import_mit_risks.py.
  Queried at audit time to enrich findings with domain-specific risks and
  enable Fixed vs Not Fixed tracking per MIT domain.

Columns mirror the MIT "AI Risk Database v3" Excel sheet columns plus the
7-domain taxonomy mapping (domain / sub_domain).
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'mit_risks',
        sa.Column('id',               sa.Integer(),     nullable=False, autoincrement=True),
        sa.Column('ev_id',            sa.String(32),    nullable=True),
        sa.Column('paper_id',         sa.String(64),    nullable=True),
        sa.Column('category_level',   sa.String(64),    nullable=True),
        sa.Column('risk_category',    sa.String(255),   nullable=True),
        sa.Column('risk_subcategory', sa.String(255),   nullable=True),
        sa.Column('description',      sa.Text(),        nullable=True),
        sa.Column('additional_ev',    sa.Text(),        nullable=True),
        sa.Column('causal_entity',    sa.String(64),    nullable=True),
        sa.Column('causal_intent',    sa.String(64),    nullable=True),
        sa.Column('causal_timing',    sa.String(64),    nullable=True),
        sa.Column('domain',           sa.String(128),   nullable=True),
        sa.Column('sub_domain',       sa.String(255),   nullable=True),
        sa.Column('created_at',       sa.DateTime(),    nullable=True),
        sa.Column('updated_at',       sa.DateTime(),    nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mit_risks_ev_id',  'mit_risks', ['ev_id'],  unique=False)
    op.create_index('ix_mit_risks_domain', 'mit_risks', ['domain'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_mit_risks_domain', table_name='mit_risks')
    op.drop_index('ix_mit_risks_ev_id',  table_name='mit_risks')
    op.drop_table('mit_risks')
