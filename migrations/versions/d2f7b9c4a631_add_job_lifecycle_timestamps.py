"""add job lifecycle timestamps

Revision ID: d2f7b9c4a631
Revises: 8b0a3f2c7d11
Create Date: 2026-06-23
"""

from alembic import op
import sqlalchemy as sa


revision = "d2f7b9c4a631"
down_revision = "8b0a3f2c7d11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job", sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("job", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("job", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("job", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("job", "cancelled_at")
    op.drop_column("job", "completed_at")
    op.drop_column("job", "started_at")
    op.drop_column("job", "assigned_at")
