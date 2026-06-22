from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router()


@router.message()
async def payload_kg(
    message: Message,
    state: FSMContext,
) -> None:

    try:
        payload = int(message.text)
    except Exception:
        return

    if payload <= 0:
        return

    await state.update_data(
        payload_kg=payload
    )

    await message.answer(
        "Объём кузова (м³)?"
    )
