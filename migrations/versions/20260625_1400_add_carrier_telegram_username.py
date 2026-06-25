"""add carrier telegram username

Revision ID: carrier_username_1400
Revises: client_ban_layer1
Create Date: 2026-06-25 14:00:00.000000+00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "carrier_username_1400"
down_revision = "client_ban_layer1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("carrier_company", sa.Column("telegram_username", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("carrier_company", "telegram_username")
