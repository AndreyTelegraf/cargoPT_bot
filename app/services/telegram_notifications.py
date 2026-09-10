import json
import logging
from datetime import UTC
from datetime import datetime
from enum import StrEnum

from app.models.telegram_notification import TelegramNotificationOutbox
from app.repositories.telegram_notification import TelegramNotificationRepository
from app.services.job_escalation import build_offer_escalation_text
from app.services.offer_notification import build_offer_text


logger = logging.getLogger(__name__)


class TelegramNotificationType(StrEnum):
    CARRIER_OFFER = "carrier_offer"
    MANUAL_REVIEW = "manual_review"


class TelegramDeliveryStatus(StrEnum):
    PENDING = "pending"
    SENDING = "sending"
    RETRY = "retry"
    SENT = "sent"
    FAILED = "failed"


class TelegramNotificationEnqueueService:
    def __init__(
        self,
        repository: TelegramNotificationRepository,
        *,
        job_repository,
        carrier_repository,
    ) -> None:
        self.repository = repository
        self.job_repository = job_repository
        self.carrier_repository = carrier_repository

    async def enqueue_carrier_offers(
        self,
        *,
        job,
        offers,
        now: datetime | None = None,
    ) -> list[TelegramNotificationOutbox]:
        timestamp = now or datetime.now(UTC)
        items = await self.job_repository.list_items_by_job(job.id)
        addresses = await self.job_repository.list_addresses_by_job(job.id)
        pickup = next(
            (address for address in addresses if address.kind == "pickup"),
            None,
        )
        dropoff = next(
            (address for address in addresses if address.kind == "dropoff"),
            None,
        )
        offer_text = build_offer_text(job, items, pickup, dropoff)
        stored_notifications = []

        for offer in offers:
            carrier = await self.carrier_repository.get_carrier_by_vehicle_id(
                offer.vehicle_id
            )
            if carrier is None or carrier.telegram_user_id is None:
                continue

            notification = TelegramNotificationOutbox(
                job_id=job.id,
                offer_id=offer.id,
                notification_type=TelegramNotificationType.CARRIER_OFFER.value,
                recipient_chat_id=carrier.telegram_user_id,
                dedupe_key=f"job:{job.id}:offer:{offer.id}:carrier_initial",
                payload_json=json.dumps(
                    {
                        "text": offer_text,
                        "parse_mode": "HTML",
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                delivery_status=TelegramDeliveryStatus.PENDING.value,
                attempt_count=0,
                next_attempt_at=timestamp,
                last_attempt_at=None,
                sent_at=None,
                provider_chat_id=None,
                provider_message_id=None,
                last_error=None,
                created_at=timestamp,
                updated_at=timestamp,
            )
            stored = await self.repository.enqueue(notification)
            stored_notifications.append(stored)
            if stored is notification:
                logger.info(
                    "telegram_notification_enqueued",
                    extra={
                        "job_id": job.id,
                        "offer_id": offer.id,
                        "notification_type": notification.notification_type,
                        "delivery_status": notification.delivery_status,
                    },
                )

        return stored_notifications

    async def enqueue_manual_review(
        self,
        *,
        job,
        offers,
        recipient_chat_ids,
        matching_reason=None,
        matching_regions=None,
        now: datetime | None = None,
    ) -> list[TelegramNotificationOutbox]:
        timestamp = now or datetime.now(UTC)
        text = build_offer_escalation_text(
            job=job,
            offers=offers,
            matching_reason=matching_reason,
            matching_regions=matching_regions,
        )
        stored_notifications = []

        for recipient_chat_id in recipient_chat_ids:
            notification = TelegramNotificationOutbox(
                job_id=job.id,
                offer_id=None,
                notification_type=TelegramNotificationType.MANUAL_REVIEW.value,
                recipient_chat_id=recipient_chat_id,
                dedupe_key=f"job:{job.id}:manual_review:{recipient_chat_id}",
                payload_json=json.dumps(
                    {"text": text},
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                delivery_status=TelegramDeliveryStatus.PENDING.value,
                attempt_count=0,
                next_attempt_at=timestamp,
                last_attempt_at=None,
                sent_at=None,
                provider_chat_id=None,
                provider_message_id=None,
                last_error=None,
                created_at=timestamp,
                updated_at=timestamp,
            )
            stored = await self.repository.enqueue(notification)
            stored_notifications.append(stored)
            if stored is notification:
                logger.info(
                    "telegram_notification_enqueued",
                    extra={
                        "job_id": job.id,
                        "notification_type": notification.notification_type,
                        "delivery_status": notification.delivery_status,
                    },
                )

        return stored_notifications
