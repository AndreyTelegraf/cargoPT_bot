from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.job_request import JobRequestStates
from app.db.session import async_session_maker
from app.repositories.job import JobRepository
from app.services.job import JobService

router = Router()


@router.message(JobRequestStates.estimated_payload_kg)
async def job_estimated_payload(
    message: Message,
    state: FSMContext,
) -> None:
    raw_value = (message.text or "").strip()

    try:
        value = int(raw_value)
    except ValueError:
        await message.answer("Укажите вес числом в кг. Если не знаете — 0.")
        return

    if value < 0:
        await message.answer("Вес не может быть отрицательным.")
        return

    estimated_payload_kg = value or None

    data = await state.get_data()
    job_id = data["job_id"]

    async with async_session_maker() as session:
        repository = JobRepository(session)
        service = JobService(repository)

        await service.update_estimated_payload(
            job_id=job_id,
            estimated_payload_kg=estimated_payload_kg,
        )

        await session.commit()

    await state.set_state(JobRequestStates.estimated_volume_m3)

    await message.answer(
        "Примерный объём груза в м³? Если не знаете — напишите 0."
    )
