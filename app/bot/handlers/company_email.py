from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router()


@router.message()
async def company_email(
    message: Message,
    state: FSMContext,
) -> None:

    email = message.text.strip()

    if "@" not in email or "." not in email:
        return

    await state.update_data(
        company_email=email
    )

    await message.answer(
        "Онбординг почти завершён. Теперь нужно сохранить транспорт в БД."
    )
