"""add job offer decline reason"""

from alembic import op
import sqlalchemy as sa


revision = "20260627_1505_decline_reason"
down_revision = "carrier_username_1400"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_offer", sa.Column("decline_reason", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("job_offer", "decline_reason")
