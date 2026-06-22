from aiogram import Router
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router()


@router.message(F.text.in_(["Да", "Нет"]))
async def mobile_lift(
    message: Message,
    state: FSMContext,
) -> None:

    await state.update_data(
        has_mobile_lift=(message.text == "Да")
    )

    await message.answer(
        "На какой максимальный этаж может подавать мобильный лифт?"
    )
