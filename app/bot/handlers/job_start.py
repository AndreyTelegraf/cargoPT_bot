from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.job_request import JobRequestStates
from app.db.session import async_session_maker
from app.repositories.job import JobRepository
from app.services.job import JobService

router = Router()


@router.message(Command("new_job"))
async def start_job_request(
    message: Message,
    state: FSMContext,
) -> None:
    async with async_session_maker() as session:
        repository = JobRepository(session)
        service = JobService(repository)

        job = await service.create_draft_job(
            client_telegram_user_id=message.from_user.id,
        )

        await session.commit()

    await state.set_state(JobRequestStates.pickup_address)
    await state.update_data(job_id=job.id)

    await message.answer(
        "Откуда забрать груз? Укажите адрес или ссылку на геолокацию."
    )
