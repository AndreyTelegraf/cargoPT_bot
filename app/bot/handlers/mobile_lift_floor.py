from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router()


@router.message()
async def mobile_lift_floor(
    message: Message,
    state: FSMContext,
) -> None:

    try:
        floor = int(message.text)
    except Exception:
        return

    if floor < 0:
        return

    await state.update_data(
        mobile_lift_max_floor=floor
    )

    await message.answer(
        "Какой максимальный вес может поднять мобильный лифт (кг)?"
    )
