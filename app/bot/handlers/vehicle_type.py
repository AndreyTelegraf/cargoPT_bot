from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.carrier_onboarding import CarrierOnboardingStates

router = Router()

ALLOWED_TYPES = {
    "Carrinha",
    "Van",
    "Camião",
    "Camião+Reboque",
}


@router.message(CarrierOnboardingStates.vehicle_type)
async def vehicle_type(
    message: Message,
    state: FSMContext,
) -> None:

    if message.text not in ALLOWED_TYPES:
        return

    await state.update_data(
        vehicle_type=message.text
    )

    await message.answer(
        "Грузоподъёмность автомобиля (кг)?"
    )
