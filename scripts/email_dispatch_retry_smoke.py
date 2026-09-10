import asyncio
from datetime import UTC
from datetime import datetime
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.base import Base
import app.models
from app.models.job import Job
from app.models.job_email_notification import JobEmailNotification
from app.repositories.job_email_notification import (
    JobEmailNotificationRepository,
)
from app.services.email.dispatcher import EmailDispatcher
from app.services.email.models import EmailDeliveryStatus
from app.services.email.models import EmailEventType
from app.services.email.models import EmailSendResult
from app.services.email.notification_service import EmailNotificationService
from app.services.email.transport import TemporaryEmailTransportError


class RetryThenSuccessTransport:
    def __init__(self) -> None:
        self.calls = 0
        self.messages = []

    async def send(self, message):
        self.calls += 1
        self.messages.append(message)
        if self.calls == 1:
            raise TemporaryEmailTransportError("temporary")
        return EmailSendResult(provider_message_id="provider-123")


class AlwaysFailTransport:
    def __init__(self) -> None:
        self.calls = 0

    async def send(self, message):
        self.calls += 1
        raise TemporaryEmailTransportError("temporary")


def make_dispatcher(sessions, transport, *, max_attempts=2):
    return EmailDispatcher(
        session_maker=sessions,
        transport=transport,
        public_base_url="https://cargopt.pt",
        from_name="CargoPT",
        from_address="noreply@cargopt.pt",
        reply_to=None,
        max_attempts=max_attempts,
        retry_base_seconds=1,
        stale_sending_seconds=300,
    )


async def enqueue(sessions, email, event_type):
    now = datetime.now(UTC)
    async with sessions() as session:
        job = Job(
            source="web_form",
            source_locale="ru",
            customer_email=email,
            status="matching",
            tracking_token=f"token-{email}-{event_type.value}",
            created_at=now,
            updated_at=now,
        )
        session.add(job)
        await session.flush()
        service = EmailNotificationService(
            JobEmailNotificationRepository(session),
            enabled=True,
        )
        notification = await service.enqueue_for_job(
            job=job,
            event_type=event_type,
            now=now,
        )
        await session.commit()
        return notification.id


async def make_due(sessions, notification_id):
    async with sessions() as session:
        notification = await session.get(
            JobEmailNotification,
            notification_id,
        )
        notification.next_attempt_at = datetime.now(UTC) - timedelta(seconds=1)
        await session.commit()


async def load(sessions, notification_id):
    async with sessions() as session:
        return await session.scalar(
            select(JobEmailNotification).where(
                JobEmailNotification.id == notification_id
            )
        )


async def claim_at(sessions, notification_id, *, claimed_at, max_attempts):
    async with sessions() as session:
        repository = JobEmailNotificationRepository(session)
        notification = await repository.claim(
            notification_id=notification_id,
            now=claimed_at,
            max_attempts=max_attempts,
        )
        assert notification is not None
        await session.commit()


async def main() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    notification_id = await enqueue(
        sessions,
        "retry@example.test",
        EmailEventType.REQUEST_RECEIVED,
    )
    transport = RetryThenSuccessTransport()
    dispatcher = make_dispatcher(sessions, transport)

    assert await dispatcher.dispatch_due() == 1
    after_first = await load(sessions, notification_id)
    assert after_first.delivery_status == EmailDeliveryStatus.RETRY.value
    assert after_first.attempt_count == 1
    assert after_first.next_attempt_at is not None

    await make_due(sessions, notification_id)
    assert await dispatcher.dispatch_due() == 1
    after_second = await load(sessions, notification_id)
    assert after_second.delivery_status == EmailDeliveryStatus.SENT.value
    assert after_second.attempt_count == 2
    assert after_second.provider_message_id == "provider-123"
    assert transport.calls == 2
    assert "/ru/track/" in transport.messages[0].text_body

    failed_id = await enqueue(
        sessions,
        "failed@example.test",
        EmailEventType.REQUEST_CANCELLED,
    )
    failure_transport = AlwaysFailTransport()
    failure_dispatcher = make_dispatcher(
        sessions,
        failure_transport,
        max_attempts=2,
    )
    assert await failure_dispatcher.dispatch_due() == 1
    await make_due(sessions, failed_id)
    assert await failure_dispatcher.dispatch_due() == 1
    failed = await load(sessions, failed_id)
    assert failed.delivery_status == EmailDeliveryStatus.FAILED.value
    assert failed.attempt_count == 2
    assert failed.next_attempt_at is None
    assert failure_transport.calls == 2
    assert await failure_dispatcher.dispatch_due() == 0

    stale_id = await enqueue(
        sessions,
        "stale@example.test",
        EmailEventType.REQUEST_RECEIVED,
    )
    await claim_at(
        sessions,
        stale_id,
        claimed_at=datetime.now(UTC) - timedelta(minutes=10),
        max_attempts=2,
    )
    stale_transport = RetryThenSuccessTransport()
    stale_transport.calls = 1
    restarted_dispatcher = make_dispatcher(sessions, stale_transport)
    assert await restarted_dispatcher.dispatch_due() == 1
    recovered = await load(sessions, stale_id)
    assert recovered.delivery_status == EmailDeliveryStatus.SENT.value
    assert recovered.attempt_count == 2
    assert recovered.provider_message_id == "provider-123"

    exhausted_id = await enqueue(
        sessions,
        "stale-exhausted@example.test",
        EmailEventType.REQUEST_CANCELLED,
    )
    await claim_at(
        sessions,
        exhausted_id,
        claimed_at=datetime.now(UTC) - timedelta(minutes=10),
        max_attempts=1,
    )
    exhausted_transport = AlwaysFailTransport()
    exhausted_dispatcher = make_dispatcher(
        sessions,
        exhausted_transport,
        max_attempts=1,
    )
    assert await exhausted_dispatcher.dispatch_due() == 0
    exhausted = await load(sessions, exhausted_id)
    assert exhausted.delivery_status == EmailDeliveryStatus.FAILED.value
    assert exhausted.last_error == "stale sending claim exhausted"
    assert exhausted_transport.calls == 0

    await engine.dispose()
    print("EMAIL_RETRY_OK")
    print("EMAIL_PERMANENT_FAILURE_OK")
    print("EMAIL_STALE_CLAIM_RECOVERY_OK")


asyncio.run(main())
