from aiogram import F
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.job_request_keyboards import yes_no_keyboard

from app.bot.states.job_request import JobRequestStates
from app.db.session import async_session_maker
from app.repositories.job import JobRepository
from app.services.job import JobService

router = Router()


@router.message(JobRequestStates.needs_tail_lift, F.text.in_(["Да", "Нет"]))
async def job_needs_tail_lift(
    message: Message,
    state: FSMContext,
) -> None:
    needs_tail_lift = message.text == "Да"

    data = await state.get_data()
    job_id = data["job_id"]

    async with async_session_maker() as session:
        repository = JobRepository(session)
        service = JobService(repository)

        await service.update_needs_tail_lift(
            job_id=job_id,
            needs_tail_lift=needs_tail_lift,
        )

        await session.commit()

    await state.set_state(JobRequestStates.needs_crane)

    await message.answer(
        "Нужен ли кран?\n\n"
        "Кран нужен, если груз нельзя занести обычным способом: очень тяжёлый предмет, палета, оборудование, подача с улицы.\n"
        "Для обычного квартирного переезда чаще всего кран не нужен.",
        reply_markup=yes_no_keyboard(),
    )
