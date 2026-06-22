from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.job_request import JobRequestStates
from app.db.session import async_session_maker
from app.repositories.job import JobRepository
from app.services.job import JobService

router = Router()


@router.message(JobRequestStates.comment)
async def job_comment(
    message: Message,
    state: FSMContext,
) -> None:
    raw_comment = (message.text or "").strip()
    comment = None if raw_comment in {"", "-"} else raw_comment

    data = await state.get_data()
    job_id = data["job_id"]

    async with async_session_maker() as session:
        repository = JobRepository(session)
        service = JobService(repository)

        await service.finalize_for_matching(
            job_id=job_id,
            comment=comment,
        )

        await session.commit()

    await state.clear()

    await message.answer(
        "Заявка сохранена. Сейчас подберём подходящих перевозчиков."
    )
