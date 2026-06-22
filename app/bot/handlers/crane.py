from aiogram import Router
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.carrier_onboarding import CarrierOnboardingStates

router = Router()


@router.message(CarrierOnboardingStates.has_crane, F.text.in_(["Да", "Нет"]))
async def crane(
    message: Message,
    state: FSMContext,
) -> None:

    await state.update_data(
        has_crane=(message.text == "Да")
    )

    await message.answer(
        "Есть ли мобильный лифт для подачи через окна? (Да/Нет)"
    )
