from aiogram import F
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton
from aiogram.types import Message
from aiogram.types import ReplyKeyboardMarkup
from aiogram.types import ReplyKeyboardRemove

from app.bot.states.carrier_onboarding import CarrierOnboardingStates

router = Router()

ALLOWED_TYPES = {
    "Carrinha",
    "Van",
    "Camião",
    "Camião+Reboque",
}


def vehicle_type_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Carrinha"), KeyboardButton(text="Van")],
            [KeyboardButton(text="Camião"), KeyboardButton(text="Camião+Reboque")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


@router.message(CarrierOnboardingStates.vehicle_type, F.text)
async def vehicle_type(
    message: Message,
    state: FSMContext,
) -> None:
    if message.text not in ALLOWED_TYPES:
        await message.answer(
            "Выберите тип автомобиля кнопкой.",
            reply_markup=vehicle_type_keyboard(),
        )
        return

    data = await state.get_data()
    current_index = data.get("current_vehicle_index", 1)
    total_count = data.get("vehicle_count", 1)

    await state.update_data(
        vehicle_type=message.text
    )

    await state.set_state(CarrierOnboardingStates.payload_kg)

    await message.answer(
        f"Автомобиль {current_index} из {total_count}.\n\n"
        "Грузоподъёмность автомобиля в кг?",
        reply_markup=ReplyKeyboardRemove(),
    )
