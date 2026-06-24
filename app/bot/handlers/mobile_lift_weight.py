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

    await state.set_state(CarrierOnboardingStates.max_loaders)

    await message.answer(
        "Шаг 4 из 6. Команда.\n\n"
        "Сколько грузчиков одновременно вы можете предоставить на один заказ?"
    )
