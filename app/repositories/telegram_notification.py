from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telegram_notification import TelegramNotificationOutbox


class TelegramNotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_dedupe_key(
        self,
        dedupe_key: str,
    ) -> TelegramNotificationOutbox | None:
        result = await self.session.execute(
            select(TelegramNotificationOutbox).where(
                TelegramNotificationOutbox.dedupe_key == dedupe_key
            )
        )
        return result.scalar_one_or_none()

    async def enqueue(
        self,
        notification: TelegramNotificationOutbox,
    ) -> TelegramNotificationOutbox:
        existing = await self.get_by_dedupe_key(notification.dedupe_key)
        if existing is not None:
            return existing

        try:
            async with self.session.begin_nested():
                self.session.add(notification)
                await self.session.flush()
            return notification
        except IntegrityError:
            existing = await self.get_by_dedupe_key(notification.dedupe_key)
            if existing is None:
                raise
            return existing
