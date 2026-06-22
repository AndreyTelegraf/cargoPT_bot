from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.job_request import JobRequestStates
from app.db.session import async_session_maker
from app.repositories.job import JobRepository
from app.services.job import JobService

router = Router()


@router.message(JobRequestStates.estimated_volume_m3)
async def job_estimated_volume(
    message: Message,
    state: FSMContext,
) -> None:
    raw_value = (message.text or "").strip().replace(",", ".")

    try:
        value = float(raw_value)
    except ValueError:
        await message.answer("Укажите объём числом в м³. Если не знаете — 0.")
        return

    if value < 0:
        await message.answer("Объём не может быть отрицательным.")
        return

    estimated_volume_m3 = value or None

    data = await state.get_data()
    job_id = data["job_id"]

    async with async_session_maker() as session:
        repository = JobRepository(session)
        service = JobService(repository)

        await service.update_estimated_volume(
            job_id=job_id,
            estimated_volume_m3=estimated_volume_m3,
        )

        await session.commit()

    await state.set_state(JobRequestStates.required_loaders)

    await message.answer(
        "Сколько грузчиков нужно? Если не знаете — напишите 0."
    )
