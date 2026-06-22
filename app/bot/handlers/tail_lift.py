from aiogram import Router
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.carrier_onboarding import CarrierOnboardingStates

router = Router()


@router.message(CarrierOnboardingStates.has_tail_lift, F.text.in_(["Да", "Нет"]))
async def tail_lift(
    message: Message,
    state: FSMContext,
) -> None:

    await state.update_data(
        has_tail_lift=(message.text == "Да")
    )

    await message.answer(
        "Есть ли кран? (Да/Нет)"
    )
