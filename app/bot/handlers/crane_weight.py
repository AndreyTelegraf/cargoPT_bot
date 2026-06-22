from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.carrier_onboarding import CarrierOnboardingStates

router = Router()


@router.message(CarrierOnboardingStates.crane_max_weight_kg)
async def crane_weight(
    message: Message,
    state: FSMContext,
) -> None:

    try:
        weight = int(message.text)
    except Exception:
        return

    if weight <= 0:
        return

    await state.update_data(
        crane_max_weight_kg=weight
    )

    await message.answer(
        "Какой максимальный вылет стрелы крана (метры)?"
    )
