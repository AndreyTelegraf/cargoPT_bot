from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.handlers.job_start import start_job_request_entry

router = Router()


@router.message(CommandStart())
async def start_handler(
    message: Message,
    state: FSMContext,
) -> None:
    await start_job_request_entry(message, state)
