"""add job media

Revision ID: 4f7c8b2a1d90
Revises: 9a35b8e7f183
Create Date: 2026-06-22 22:05:00.000000
"""

from typing import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "4f7c8b2a1d90"
down_revision: Union[str, Sequence[str], None] = "9a35b8e7f183"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_media",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("media_type", sa.String(), nullable=False),
        sa.Column("telegram_file_id", sa.String(), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["job.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_media_job_id", "job_media", ["job_id"], unique=False)
    op.create_index("ix_job_media_media_type", "job_media", ["media_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_job_media_media_type", table_name="job_media")
    op.drop_index("ix_job_media_job_id", table_name="job_media")
    op.drop_table("job_media")
