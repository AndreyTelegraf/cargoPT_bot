from aiogram import Router
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.handlers.invite import carrier_yes_no_keyboard
from app.bot.states.carrier_onboarding import CarrierOnboardingStates

router = Router()


@router.message(CarrierOnboardingStates.has_crane, F.text.in_(["Да", "Нет"]))
async def crane(
    message: Message,
    state: FSMContext,
) -> None:

    has_crane = message.text == "Да"

    await state.update_data(
        has_crane=has_crane
    )

    if has_crane:
        await state.set_state(CarrierOnboardingStates.crane_max_weight_kg)
        await message.answer(
            "Какой максимальный вес может поднять кран в кг?"
        )
        return

    await state.set_state(CarrierOnboardingStates.has_mobile_lift)

    await message.answer(
        "Есть ли мобильный лифт для подачи через окна?",
        reply_markup=carrier_yes_no_keyboard(),
    )
