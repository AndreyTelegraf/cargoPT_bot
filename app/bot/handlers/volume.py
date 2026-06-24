from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.handlers.invite import carrier_yes_no_keyboard
from app.bot.states.carrier_onboarding import CarrierOnboardingStates

router = Router()


@router.message(CarrierOnboardingStates.volume_m3)
async def volume_m3(
    message: Message,
    state: FSMContext,
) -> None:

    try:
        volume = float(
            message.text.replace(",", ".")
        )
    except Exception:
        return

    if volume <= 0:
        return

    await state.update_data(
        volume_m3=volume
    )

    await state.set_state(CarrierOnboardingStates.has_tail_lift)

    await message.answer(
        "Есть ли гидроборт?",
        reply_markup=carrier_yes_no_keyboard(),
    )
