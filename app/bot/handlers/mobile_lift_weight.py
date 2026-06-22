from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.carrier_onboarding import CarrierOnboardingStates

router = Router()


@router.message(CarrierOnboardingStates.mobile_lift_max_weight_kg)
async def mobile_lift_weight(
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
        mobile_lift_max_weight_kg=weight
    )

    await message.answer(
        "Какой максимальный вес может поднять кран (кг)?"
    )
