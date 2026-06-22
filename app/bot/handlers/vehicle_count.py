from aiogram import Router
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router()


@router.message(F.text.regexp(r"^[1-9][0-9]*$"))
async def vehicle_count(
    message: Message,
    state: FSMContext,
) -> None:
    await state.update_data(
        vehicle_count=int(message.text)
    )

    await message.answer(
        "Укажите тип первого автомобиля."
    )

print("VEHICLE_COUNT_HANDLER_LOADED")
