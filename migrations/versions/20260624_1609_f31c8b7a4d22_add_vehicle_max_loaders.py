"""add vehicle max loaders

Revision ID: f31c8b7a4d22
Revises: 366e4e214c8f
Create Date: 2026-06-24 16:09:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "f31c8b7a4d22"
down_revision = "366e4e214c8f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "carrier_vehicle",
        sa.Column("max_loaders", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("carrier_vehicle", "max_loaders")
