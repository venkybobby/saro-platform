"""SARO v9.3 — Audit tracing columns + evidence package

Revision ID: 0007
Revises: 0006
Create Date: 2026-03-24

Adds tracing columns to the audits table:
- rules_version         — which version of the 1,664 rules was applied
- evidence_package_url  — S3 URL (or inline path) to immutable evidence package
- batch_sample_count    — number of batch records processed in this audit
- retention_until       — 7-year retention deadline (EU AI Act / ISO 42001 Clause 10)
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0007'
down_revision: Union[str, None] = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('audits', sa.Column('rules_version',        sa.String(16),  nullable=True, server_default='1.0'))
    op.add_column('audits', sa.Column('evidence_package_url', sa.Text(),       nullable=True))
    op.add_column('audits', sa.Column('batch_sample_count',   sa.Integer(),    nullable=True))
    op.add_column('audits', sa.Column('retention_until',      sa.DateTime(),   nullable=True))


def downgrade() -> None:
    op.drop_column('audits', 'retention_until')
    op.drop_column('audits', 'batch_sample_count')
    op.drop_column('audits', 'evidence_package_url')
    op.drop_column('audits', 'rules_version')
