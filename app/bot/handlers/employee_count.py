from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router()


@router.message()
async def employee_count(
    message: Message,
    state: FSMContext,
) -> None:

    try:
        employees = int(message.text)
    except Exception:
        return

    if employees <= 0:
        return

    await state.update_data(
        employee_count=employees
    )

    await message.answer(
        "Сколько грузчиков одновременно вы можете предоставить на один заказ?"
    )
