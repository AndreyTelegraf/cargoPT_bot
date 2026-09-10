"""add comparable offer terms

Revision ID: 20260910_1930_offer_terms
Revises: 20260910_1600_telegram_outbox
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260910_1930_offer_terms"
down_revision: str | None = "20260910_1600_telegram_outbox"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "job_offer",
        sa.Column("included_services", sa.Text(), nullable=True),
    )
    op.add_column(
        "job_offer",
        sa.Column("possible_surcharges", sa.Text(), nullable=True),
    )
    op.add_column(
        "job_offer",
        sa.Column("service_window", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "job_offer",
        sa.Column("estimate_status", sa.String(length=32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("job_offer", "estimate_status")
    op.drop_column("job_offer", "service_window")
    op.drop_column("job_offer", "possible_surcharges")
    op.drop_column("job_offer", "included_services")
