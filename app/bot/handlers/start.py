from aiogram import F
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.handlers.job_start import start_job_request

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    await start_job_request(message, state)


@router.message(F.text == "Помощь")
async def help_placeholder(message: Message) -> None:
    await message.answer(
        "Помощь скоро появится.\n\n"
        "Сейчас для создания заявки нажмите /start или /new_job."
    )


@router.message(F.text == "Мои объявления")
async def my_ads_placeholder(message: Message) -> None:
    await message.answer(
        "Раздел «Мои объявления» скоро появится.\n\n"
        "Сейчас активные заявки обрабатываются диспетчером CargoPT."
    )
