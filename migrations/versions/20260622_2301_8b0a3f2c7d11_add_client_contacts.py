"""add client contacts

Revision ID: 8b0a3f2c7d11
Revises: 4f7c8b2a1d90
Create Date: 2026-06-22 23:01:00.000000
"""

from typing import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "8b0a3f2c7d11"
down_revision: Union[str, None] = "4f7c8b2a1d90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("job", sa.Column("client_telegram_username", sa.String(), nullable=True))
    op.add_column("job", sa.Column("client_phone", sa.String(), nullable=True))
    op.add_column("job", sa.Column("client_whatsapp", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("job", "client_whatsapp")
    op.drop_column("job", "client_phone")
    op.drop_column("job", "client_telegram_username")
