import asyncio

from app.bot.dispatcher import build_dispatcher

async def run() -> None:
    bot, dp = build_dispatcher()
    await dp.start_polling(bot)

def main() -> None:
    asyncio.run(run())

if __name__ == "__main__":
    main()
