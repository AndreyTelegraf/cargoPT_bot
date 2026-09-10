"""add durable Telegram notification outbox

Revision ID: 20260910_1600_telegram_outbox
Revises: 20260910_1500_web_idempotency
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260910_1600_telegram_outbox"
down_revision: str | None = "20260910_1500_web_idempotency"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "telegram_notification_outbox",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("offer_id", sa.Integer(), nullable=True),
        sa.Column("notification_type", sa.String(length=40), nullable=False),
        sa.Column("recipient_chat_id", sa.BigInteger(), nullable=False),
        sa.Column("dedupe_key", sa.String(length=160), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("delivery_status", sa.String(length=20), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("provider_message_id", sa.BigInteger(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["job.id"]),
        sa.ForeignKeyConstraint(["offer_id"], ["job_offer.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_telegram_notification_job_id",
        "telegram_notification_outbox",
        ["job_id"],
    )
    op.create_index(
        "ix_telegram_notification_offer_id",
        "telegram_notification_outbox",
        ["offer_id"],
    )
    op.create_index(
        "ix_telegram_notification_status",
        "telegram_notification_outbox",
        ["delivery_status"],
    )
    op.create_index(
        "ix_telegram_notification_next_attempt",
        "telegram_notification_outbox",
        ["next_attempt_at"],
    )
    op.create_index(
        "ux_telegram_notification_dedupe_key",
        "telegram_notification_outbox",
        ["dedupe_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ux_telegram_notification_dedupe_key",
        table_name="telegram_notification_outbox",
    )
    op.drop_index(
        "ix_telegram_notification_next_attempt",
        table_name="telegram_notification_outbox",
    )
    op.drop_index(
        "ix_telegram_notification_status",
        table_name="telegram_notification_outbox",
    )
    op.drop_index(
        "ix_telegram_notification_offer_id",
        table_name="telegram_notification_outbox",
    )
    op.drop_index(
        "ix_telegram_notification_job_id",
        table_name="telegram_notification_outbox",
    )
    op.drop_table("telegram_notification_outbox")
