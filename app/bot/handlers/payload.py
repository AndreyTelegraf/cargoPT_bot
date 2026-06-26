from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.carrier_onboarding import CarrierOnboardingStates
from app.services.input_normalization import parse_first_int

router = Router()


@router.message(CarrierOnboardingStates.payload_kg)
async def payload_kg(
    message: Message,
    state: FSMContext,
) -> None:

    try:
        payload = parse_first_int(message.text)
    except Exception:
        return

    if payload <= 0:
        return

    await state.update_data(
        payload_kg=payload
    )

    await state.set_state(CarrierOnboardingStates.volume_m3)

    await message.answer(
        "Объём кузова в м³?"
    )
