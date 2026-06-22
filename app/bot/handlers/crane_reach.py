from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router()


@router.message()
async def crane_reach(
    message: Message,
    state: FSMContext,
) -> None:

    try:
        reach = int(message.text)
    except Exception:
        return

    if reach <= 0:
        return

    await state.update_data(
        crane_max_reach_m=reach
    )

    await message.answer(
        "Сколько сотрудников работает в вашей компании?"
    )
