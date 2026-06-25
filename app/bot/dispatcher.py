from aiogram import Bot
from aiogram import Dispatcher

from app.bot.middleware.self_ad import SelfAdMiddleware
from app.bot.routers import setup_routers
from app.config import settings


def build_dispatcher() -> tuple[Bot, Dispatcher]:
    bot = Bot(settings.bot_token)
    dp = Dispatcher()
    dp.update.outer_middleware(SelfAdMiddleware())
    setup_routers(dp)
    return bot, dp
