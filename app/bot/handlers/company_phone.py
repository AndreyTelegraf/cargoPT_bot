from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.carrier_onboarding import CarrierOnboardingStates

router = Router()


@router.message(CarrierOnboardingStates.company_phone)
async def company_phone(
    message: Message,
    state: FSMContext,
) -> None:

    phone = message.text.strip()

    if len(phone) < 6:
        return

    await state.update_data(
        company_phone=phone
    )

    await state.set_state(CarrierOnboardingStates.company_email)

    await message.answer(
        "Укажите контактный email компании."
    )
