from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router()


@router.message()
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

    await message.answer(
        "Укажите контактный email компании"
    )
