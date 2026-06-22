from aiogram import Bot
from aiogram import Dispatcher

from app.bot.routers import setup_routers
from app.config import settings

def build_dispatcher() -> tuple[Bot, Dispatcher]:
    bot = Bot(settings.bot_token)
    dp = Dispatcher()
    setup_routers(dp)
    return bot, dp
