from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.handlers.invite import carrier_yes_no_keyboard
from app.bot.states.carrier_onboarding import CarrierOnboardingStates

router = Router()


@router.message(CarrierOnboardingStates.crane_reach_meters)
async def crane_reach(
    message: Message,
    state: FSMContext,
) -> None:

    try:
        reach = int(message.text)
    except Exception:
        return

    if reach <= 0:
        return

    await state.update_data(
        crane_max_reach_m=reach
    )

    await state.set_state(CarrierOnboardingStates.has_mobile_lift)

    await message.answer(
        "Есть ли мобильный лифт для подачи через окна?",
        reply_markup=carrier_yes_no_keyboard(),
    )
