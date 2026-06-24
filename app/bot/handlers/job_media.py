from aiogram import F
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.job_request_keyboards import media_skip_keyboard
from app.bot.job_request_keyboards import payload_keyboard

from app.bot.states.job_request import JobRequestStates
from app.db.session import async_session_maker
from app.repositories.job import JobRepository
from app.services.job import JobService

router = Router()


@router.message(JobRequestStates.media, F.photo | F.video | F.text)
async def job_media(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    job_id = data["job_id"]

    media_type = None
    telegram_file_id = None
    caption = message.caption

    if message.photo:
        media_type = "photo"
        telegram_file_id = message.photo[-1].file_id
    elif message.video:
        media_type = "video"
        telegram_file_id = message.video.file_id
    elif (message.text or "").strip() in {"-", "Пропустить медиа", "Готово с медиа"}:
        await state.set_state(JobRequestStates.estimated_payload_kg)
        await message.answer(
            "Оцените примерный вес груза.\n\n"
            "Ориентир:\n"
            "- до 500 кг — несколько коробок или небольшой переезд;\n"
            "- до 1000 кг — обычный квартирный переезд;\n"
            "- до 1600 кг — крупная мебель и техника;\n"
            "- до 3500 кг — большой объём или тяжёлый груз.\n\n"
            "Можно нажать кнопку или ввести число в кг.",
            reply_markup=payload_keyboard(),
        )
        return
    else:
        await message.answer("Пришлите фото/видео груза или нажмите «Пропустить медиа».")
        return

    async with async_session_maker() as session:
        repository = JobRepository(session)
        service = JobService(repository)

        await service.add_media(
            job_id=job_id,
            media_type=media_type,
            telegram_file_id=telegram_file_id,
            caption=caption,
        )

        await session.commit()

    await state.update_data(media_saved=True)

    if not data.get("media_ack_sent"):
        await state.update_data(media_ack_sent=True)
        await message.answer(
            "Медиа сохранено. Можно прислать ещё фото/видео или нажать «Готово с медиа».",
            reply_markup=media_skip_keyboard(),
        )
