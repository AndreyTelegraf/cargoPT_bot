import asyncio
from contextlib import suppress

from app.bot.dispatcher import build_dispatcher
from app.scheduler.offer_expiry import run_offer_expiry_loop


async def run() -> None:
    bot, dp = build_dispatcher()
    offer_expiry_task = asyncio.create_task(
        run_offer_expiry_loop(bot=bot)
    )

    try:
        await dp.start_polling(bot)
    finally:
        offer_expiry_task.cancel()
        with suppress(asyncio.CancelledError):
            await offer_expiry_task


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
