"""add durable web request idempotency fields

Revision ID: 20260910_1500_web_idempotency
Revises: 20260903_1200_short_lead_filter
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260910_1500_web_idempotency"
down_revision: str | None = "20260903_1200_short_lead_filter"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "job",
        sa.Column(
            "web_idempotency_key",
            sa.String(length=128),
            nullable=True,
        ),
    )
    op.add_column(
        "job",
        sa.Column(
            "web_request_fingerprint",
            sa.String(length=64),
            nullable=True,
        ),
    )
    op.create_index(
        "ux_job_web_idempotency_key",
        "job",
        ["web_idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_job_web_idempotency_key", table_name="job")
    op.drop_column("job", "web_request_fingerprint")
    op.drop_column("job", "web_idempotency_key")
