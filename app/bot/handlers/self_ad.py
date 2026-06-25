from aiogram import F, Router
from aiogram.types import Message

from app.services.self_ad_counter import process_self_ad_message

router = Router()


@router.message(F.text)
async def handle_self_ad_counter(message: Message) -> None:
    await process_self_ad_message(message)
