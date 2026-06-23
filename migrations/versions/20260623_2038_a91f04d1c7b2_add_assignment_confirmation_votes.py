"""add assignment confirmation votes

Revision ID: a91f04d1c7b2
Revises: d2f7b9c4a631
Create Date: 2026-06-23
"""

from alembic import op
import sqlalchemy as sa


revision = "a91f04d1c7b2"
down_revision = "d2f7b9c4a631"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job", sa.Column("client_confirmation_status", sa.String(), nullable=True))
    op.add_column("job", sa.Column("carrier_confirmation_status", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("job", "carrier_confirmation_status")
    op.drop_column("job", "client_confirmation_status")
