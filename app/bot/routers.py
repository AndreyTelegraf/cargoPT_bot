from aiogram import Dispatcher

from app.bot.handlers.start import router as start_router
from app.bot.handlers.invite import router as invite_router
from app.bot.handlers.assembly import router as assembly_router
from app.bot.handlers.packing import router as packing_router
from app.bot.handlers.regions import router as regions_router
from app.bot.handlers.vehicle_count import router as vehicle_count_router
from app.bot.handlers.vehicle_type import router as vehicle_type_router
from app.bot.handlers.payload import router as payload_router
from app.bot.handlers.volume import router as volume_router
from app.bot.handlers.tail_lift import router as tail_lift_router
from app.bot.handlers.crane import router as crane_router
from app.bot.handlers.mobile_lift import router as mobile_lift_router
from app.bot.handlers.mobile_lift_floor import router as mobile_lift_floor_router
from app.bot.handlers.mobile_lift_weight import router as mobile_lift_weight_router
from app.bot.handlers.crane_weight import router as crane_weight_router
from app.bot.handlers.crane_reach import router as crane_reach_router
from app.bot.handlers.employee_count import router as employee_count_router
from app.bot.handlers.max_loaders import router as max_loaders_router
from app.bot.handlers.company_phone import router as company_phone_router


def setup_routers(dp: Dispatcher) -> None:
    dp.include_router(invite_router)
    dp.include_router(packing_router)
    dp.include_router(regions_router)
    dp.include_router(vehicle_count_router)
    dp.include_router(vehicle_type_router)
    dp.include_router(payload_router)
    dp.include_router(volume_router)
    dp.include_router(tail_lift_router)
    dp.include_router(crane_router)
    dp.include_router(mobile_lift_router)
    dp.include_router(mobile_lift_floor_router)
    dp.include_router(mobile_lift_weight_router)
    dp.include_router(crane_weight_router)
    dp.include_router(crane_reach_router)
    dp.include_router(employee_count_router)
    dp.include_router(max_loaders_router)
    dp.include_router(company_phone_router)
    dp.include_router(assembly_router)
    dp.include_router(start_router)
