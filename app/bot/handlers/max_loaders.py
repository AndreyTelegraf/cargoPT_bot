from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.carrier_onboarding import CarrierOnboardingStates

router = Router()


@router.message(CarrierOnboardingStates.max_loaders)
async def max_loaders(
    message: Message,
    state: FSMContext,
) -> None:

    try:
        loaders = int(message.text)
    except Exception:
        return

    if loaders <= 0:
        return

    await state.update_data(
        max_loaders=loaders
    )

    await state.set_state(CarrierOnboardingStates.company_phone)

    await message.answer(
        "Шаг 5 из 6. Контакты.\n\n"
        "Какой номер телефона для связи с вашей компанией?"
    )
