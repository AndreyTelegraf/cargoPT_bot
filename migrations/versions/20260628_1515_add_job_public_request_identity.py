"""add job public request identity fields"""

from alembic import op
import sqlalchemy as sa


revision = "20260628_1515_job_public_identity"
down_revision = "20260627_1505_decline_reason"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("job") as batch_op:
        batch_op.alter_column(
            "client_telegram_user_id",
            existing_type=sa.Integer(),
            nullable=True,
        )
        batch_op.add_column(sa.Column("source", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("source_locale", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("customer_name", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("customer_email", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("preferred_contact", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("utm_source", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("utm_campaign", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("landing_version", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("job") as batch_op:
        batch_op.drop_column("landing_version")
        batch_op.drop_column("utm_campaign")
        batch_op.drop_column("utm_source")
        batch_op.drop_column("preferred_contact")
        batch_op.drop_column("customer_email")
        batch_op.drop_column("customer_name")
        batch_op.drop_column("source_locale")
        batch_op.drop_column("source")
        batch_op.alter_column(
            "client_telegram_user_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
