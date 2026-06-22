from aiogram import Dispatcher

from app.bot.handlers.start import router as start_router
from app.bot.handlers.invite import router as invite_router
from app.bot.handlers.assembly import router as assembly_router
from app.bot.handlers.packing import router as packing_router


def setup_routers(dp: Dispatcher) -> None:
    dp.include_router(invite_router)
    dp.include_router(packing_router)
    dp.include_router(assembly_router)
    dp.include_router(start_router)
