from aiogram import F
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

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
    elif (message.text or "").strip() == "-":
        await state.set_state(JobRequestStates.estimated_payload_kg)
        await message.answer("Примерный вес груза в кг? Если не знаете — напишите 0.")
        return
    else:
        await message.answer("Пришлите фото/видео груза или напишите '-' если медиа нет.")
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

    await state.set_state(JobRequestStates.estimated_payload_kg)

    await message.answer("Медиа сохранено. Примерный вес груза в кг? Если не знаете — напишите 0.")
