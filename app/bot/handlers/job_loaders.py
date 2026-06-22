from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.job_request import JobRequestStates
from app.db.session import async_session_maker
from app.repositories.job import JobRepository
from app.services.job import JobService

router = Router()


@router.message(JobRequestStates.required_loaders)
async def job_required_loaders(
    message: Message,
    state: FSMContext,
) -> None:
    raw_value = (message.text or "").strip()

    try:
        value = int(raw_value)
    except ValueError:
        await message.answer("Укажите количество грузчиков числом. Если не знаете — 0.")
        return

    if value < 0:
        await message.answer("Количество грузчиков не может быть отрицательным.")
        return

    required_loaders = value or None

    data = await state.get_data()
    job_id = data["job_id"]

    async with async_session_maker() as session:
        repository = JobRepository(session)
        service = JobService(repository)

        await service.update_required_loaders(
            job_id=job_id,
            required_loaders=required_loaders,
        )

        await session.commit()

    await state.set_state(JobRequestStates.needs_tail_lift)

    await message.answer(
        "Нужен ли гидроборт? (Да/Нет)"
    )
