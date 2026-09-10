from datetime import datetime

from sqlalchemy import BigInteger
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.db.base import Base


class TelegramNotificationOutbox(Base):
    __tablename__ = "telegram_notification_outbox"

    __table_args__ = (
        Index("ix_telegram_notification_job_id", "job_id"),
        Index("ix_telegram_notification_offer_id", "offer_id"),
        Index("ix_telegram_notification_status", "delivery_status"),
        Index("ix_telegram_notification_next_attempt", "next_attempt_at"),
        Index(
            "ux_telegram_notification_dedupe_key",
            "dedupe_key",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("job.id"),
        nullable=False,
    )
    offer_id: Mapped[int | None] = mapped_column(ForeignKey("job_offer.id"))
    notification_type: Mapped[str] = mapped_column(String(40), nullable=False)
    recipient_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(160), nullable=False)
    payload_json: Mapped[str | None] = mapped_column(Text)
    delivery_status: Mapped[str] = mapped_column(String(20), nullable=False)
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    next_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    last_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provider_chat_id: Mapped[int | None] = mapped_column(BigInteger)
    provider_message_id: Mapped[int | None] = mapped_column(BigInteger)
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
