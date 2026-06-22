from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router()


@router.message()
async def volume_m3(
    message: Message,
    state: FSMContext,
) -> None:

    try:
        volume = float(
            message.text.replace(",", ".")
        )
    except Exception:
        return

    if volume <= 0:
        return

    await state.update_data(
        volume_m3=volume
    )

    await message.answer(
        "Есть ли гидроборт? (Да/Нет)"
    )
