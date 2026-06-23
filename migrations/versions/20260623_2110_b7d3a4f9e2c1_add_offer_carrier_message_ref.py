"""add offer carrier message ref

Revision ID: b7d3a4f9e2c1
Revises: a91f04d1c7b2
Create Date: 2026-06-23
"""

from alembic import op
import sqlalchemy as sa


revision = "b7d3a4f9e2c1"
down_revision = "a91f04d1c7b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_offer", sa.Column("carrier_message_chat_id", sa.Integer(), nullable=True))
    op.add_column("job_offer", sa.Column("carrier_message_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("job_offer", "carrier_message_id")
    op.drop_column("job_offer", "carrier_message_chat_id")
