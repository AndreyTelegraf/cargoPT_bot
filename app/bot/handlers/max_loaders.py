from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router()


@router.message()
async def max_loaders(
    message: Message,
    state: FSMContext,
) -> None:

    try:
        loaders = int(message.text)
    except Exception:
        return

    if loaders <= 0:
        return

    await state.update_data(
        max_loaders=loaders
    )

    await message.answer(
        "Какой номер телефона для связи с вашей компанией?"
    )
