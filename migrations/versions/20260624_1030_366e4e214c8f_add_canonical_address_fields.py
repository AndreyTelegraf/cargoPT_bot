"""add canonical address fields

Revision ID: 366e4e214c8f
Revises: b7d3a4f9e2c1
Create Date: 2026-06-24 10:30:36.997945+00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '366e4e214c8f'
down_revision: Union[str, None] = 'b7d3a4f9e2c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "job_address",
        sa.Column("original_google_maps_url", sa.Text(), nullable=True),
    )

    op.add_column(
        "job_address",
        sa.Column("normalized_address", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("job_address", "normalized_address")
    op.drop_column("job_address", "original_google_maps_url")
