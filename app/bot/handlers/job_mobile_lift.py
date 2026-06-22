from aiogram import F
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.job_request import JobRequestStates
from app.db.session import async_session_maker
from app.repositories.job import JobRepository
from app.services.job import JobService

router = Router()


@router.message(JobRequestStates.needs_mobile_lift, F.text.in_(["Да", "Нет"]))
async def job_needs_mobile_lift(
    message: Message,
    state: FSMContext,
) -> None:
    needs_mobile_lift = message.text == "Да"

    data = await state.get_data()
    job_id = data["job_id"]

    async with async_session_maker() as session:
        repository = JobRepository(session)
        service = JobService(repository)

        await service.update_needs_mobile_lift(
            job_id=job_id,
            needs_mobile_lift=needs_mobile_lift,
        )

        await session.commit()

    await state.set_state(JobRequestStates.comment)

    await message.answer(
        "Добавьте комментарий к заказу или напишите '-' если комментария нет."
    )
