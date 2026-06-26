from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.carrier_onboarding import CarrierOnboardingStates
from app.services.input_normalization import parse_first_int

router = Router()


@router.message(CarrierOnboardingStates.crane_max_weight_kg)
async def crane_weight(
    message: Message,
    state: FSMContext,
) -> None:

    try:
        weight = parse_first_int(message.text)
    except Exception:
        return

    if weight <= 0:
        return

    await state.update_data(
        crane_max_weight_kg=weight
    )

    await state.set_state(CarrierOnboardingStates.crane_reach_meters)

    await message.answer(
        "Какой максимальный вылет стрелы крана в метрах?"
    )
