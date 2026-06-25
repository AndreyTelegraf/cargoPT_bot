"""add client ban table

Revision ID: client_ban_layer1
Revises: f31c8b7a4d22
Create Date: 2026-06-25 13:00:00.000000+00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "client_ban_layer1"
down_revision = "f31c8b7a4d22"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "client_ban",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_user_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("banned_by_admin_id", sa.Integer(), nullable=False),
        sa.Column("banned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("unbanned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unbanned_by_admin_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_client_ban_telegram_user_id", "client_ban", ["telegram_user_id"])


def downgrade() -> None:
    op.drop_index("ix_client_ban_telegram_user_id", table_name="client_ban")
    op.drop_table("client_ban")
