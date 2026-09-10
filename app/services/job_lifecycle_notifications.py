from datetime import UTC
from datetime import datetime
from datetime import timedelta

from app.domain.requested_date import PORTUGAL_TIMEZONE
from app.repositories.carrier import CarrierRepository
from app.repositories.job import JobRepository
from app.repositories.telegram_notification import TelegramNotificationRepository
from app.services.email.models import EmailEventType
from app.services.telegram_notifications import TelegramNotificationEnqueueService


def _format_requested_date(value: datetime | None) -> str:
    if value is None:
        return "не указана"
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(PORTUGAL_TIMEZONE).strftime("%d.%m.%Y %H:%M")


async def _job_party_chat_ids(
    *,
    job,
    accepted_offer,
    carrier_repository: CarrierRepository,
):
    chat_ids = []
    if job.client_telegram_user_id is not None:
        chat_ids.append(job.client_telegram_user_id)

    if accepted_offer is None:
        return chat_ids
    carrier = await carrier_repository.get_carrier_by_id(
        accepted_offer.carrier_id
    )
    if carrier is not None and carrier.telegram_user_id is not None:
        chat_ids.append(carrier.telegram_user_id)
    return chat_ids


async def process_job_lifecycle_notifications(
    *,
    bot,
    session,
    now: datetime | None = None,
    limit: int = 100,
) -> int:
    timestamp = now or datetime.now(UTC)
    job_repository = JobRepository(session)
    carrier_repository = CarrierRepository(session)
    notification_service = TelegramNotificationEnqueueService(
        TelegramNotificationRepository(session),
        job_repository=job_repository,
        carrier_repository=carrier_repository,
    )
    processed = 0

    reminder_24h_jobs = await job_repository.list_jobs_for_24h_reminder(
        now=timestamp + timedelta(hours=2),
        cutoff=timestamp + timedelta(hours=24),
        limit=limit,
    )
    for job in reminder_24h_jobs:
        accepted_offer = await job_repository.get_accepted_offer_by_job_id(job.id)
        text = (
            f"Напоминание по заявке #{job.id}.\n\n"
            f"Перевозка запланирована на {_format_requested_date(job.requested_date)}.\n"
            "Проверьте адреса и договорённости второй стороны."
        )
        chat_ids = await _job_party_chat_ids(
            job=job,
            accepted_offer=accepted_offer,
            carrier_repository=carrier_repository,
        )
        notifications = await notification_service.enqueue_lifecycle_messages(
            job=job,
            recipient_chat_ids=chat_ids,
            text=text,
            lifecycle_notification="reminder_24h",
            now=timestamp,
        )
        await job_repository.enqueue_email_notification(
            job=job,
            event_type=EmailEventType.MOVE_REMINDER_24H,
            now=timestamp,
        )
        if not notifications:
            await job_repository.mark_lifecycle_notification_sent(
                job_id=job.id,
                notification="reminder_24h",
                sent_at=timestamp,
            )
        processed += 1

    reminder_2h_jobs = await job_repository.list_jobs_for_2h_reminder(
        now=timestamp,
        cutoff=timestamp + timedelta(hours=2),
        limit=limit,
    )
    for job in reminder_2h_jobs:
        accepted_offer = await job_repository.get_accepted_offer_by_job_id(job.id)
        text = (
            f"Напоминание по заявке #{job.id}.\n\n"
            f"Перевозка запланирована на {_format_requested_date(job.requested_date)}.\n"
            "До начала осталось менее двух часов."
        )
        chat_ids = await _job_party_chat_ids(
            job=job,
            accepted_offer=accepted_offer,
            carrier_repository=carrier_repository,
        )
        notifications = await notification_service.enqueue_lifecycle_messages(
            job=job,
            recipient_chat_ids=chat_ids,
            text=text,
            lifecycle_notification="reminder_2h",
            now=timestamp,
        )
        await job_repository.enqueue_email_notification(
            job=job,
            event_type=EmailEventType.MOVE_REMINDER_2H,
            now=timestamp,
        )
        if not notifications:
            await job_repository.mark_lifecycle_notification_sent(
                job_id=job.id,
                notification="reminder_2h",
                sent_at=timestamp,
            )
        processed += 1

    completion_jobs = await job_repository.list_jobs_for_completion_prompt(
        cutoff=timestamp - timedelta(hours=2),
        not_before=timestamp - timedelta(hours=48),
        limit=limit,
    )
    for job in completion_jobs:
        accepted_offer = await job_repository.get_accepted_offer_by_job_id(job.id)
        text = (
            f"Запланированное время перевозки по заявке #{job.id} прошло.\n\n"
            "Подтвердите результат перевозки."
        )
        chat_ids = await _job_party_chat_ids(
            job=job,
            accepted_offer=accepted_offer,
            carrier_repository=carrier_repository,
        )
        notifications = await notification_service.enqueue_lifecycle_messages(
            job=job,
            recipient_chat_ids=chat_ids,
            text=text,
            lifecycle_notification="completion_prompt",
            completion_keyboard=True,
            now=timestamp,
        )
        await job_repository.enqueue_email_notification(
            job=job,
            event_type=EmailEventType.COMPLETION_REQUESTED,
            now=timestamp,
        )
        if not notifications:
            await job_repository.mark_lifecycle_notification_sent(
                job_id=job.id,
                notification="completion_prompt",
                sent_at=timestamp,
            )
        processed += 1

    return processed
