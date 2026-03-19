"""SARO v9.2 — MIT AI Risk Repository taxonomy columns on audits table

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-19

Changes:
- audits.mit_domain_tags    JSONB   — list of MIT domains covered (e.g. ["Discrimination & Toxicity"])
- audits.mit_coverage_score FLOAT   — MIT domain coverage percentage (0.0 – 100.0)
- audits.fixed_delta_mit    JSONB   — MIT coverage delta from previous audit {before_score, after_score, new_domains, improved}

These columns are populated by _persist_audit_to_db() in audit_engine.py.
Existing rows will have NULL values; the engine handles NULL gracefully via getattr().
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('audits', sa.Column('mit_domain_tags',    sa.JSON(), nullable=True))
    op.add_column('audits', sa.Column('mit_coverage_score', sa.Float(), nullable=True))
    op.add_column('audits', sa.Column('fixed_delta_mit',    sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('audits', 'fixed_delta_mit')
    op.drop_column('audits', 'mit_coverage_score')
    op.drop_column('audits', 'mit_domain_tags')
