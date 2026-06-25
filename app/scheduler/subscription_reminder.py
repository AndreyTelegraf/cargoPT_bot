import asyncio
import logging

from app.db.session import async_session_maker
from app.services.subscription_reminder import process_subscription_reminders

logger = logging.getLogger(__name__)


async def run_subscription_reminder_loop(
    *,
    bot,
    interval_seconds: int = 21600,
) -> None:
    while True:
        try:
            async with async_session_maker() as session:
                sent = await process_subscription_reminders(
                    bot=bot,
                    session=session,
                )
                if sent:
                    await session.commit()
                    logger.info("subscription_reminder_job sent %s reminders", sent)
                else:
                    await session.rollback()
        except Exception:
            logger.exception("subscription_reminder_job failed")

        await asyncio.sleep(interval_seconds)
