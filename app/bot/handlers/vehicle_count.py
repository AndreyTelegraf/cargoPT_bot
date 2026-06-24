from aiogram import F
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.handlers.vehicle_type import vehicle_type_keyboard
from app.bot.states.carrier_onboarding import CarrierOnboardingStates

router = Router()


@router.message(CarrierOnboardingStates.vehicle_count, F.text.regexp(r"^[1-9][0-9]*$"))
async def vehicle_count(
    message: Message,
    state: FSMContext,
) -> None:
    await state.update_data(
        vehicle_count=int(message.text)
    )

    await state.set_state(CarrierOnboardingStates.vehicle_type)

    await message.answer(
        "Шаг 3 из 7. Автомобиль 1.\n\n"
        "Выберите тип автомобиля.",
        reply_markup=vehicle_type_keyboard(),
    )

print("VEHICLE_COUNT_HANDLER_LOADED")
