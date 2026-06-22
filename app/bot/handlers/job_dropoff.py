from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.job_request import JobRequestStates
from app.db.session import async_session_maker
from app.repositories.job import JobRepository
from app.services.job import JobService

router = Router()


@router.message(JobRequestStates.dropoff_address)
async def job_dropoff_address(
    message: Message,
    state: FSMContext,
) -> None:
    raw_text = (message.text or "").strip()

    if not raw_text:
        await message.answer("Укажите адрес или ссылку на геолокацию.")
        return

    data = await state.get_data()
    job_id = data["job_id"]

    async with async_session_maker() as session:
        repository = JobRepository(session)
        service = JobService(repository)

        await service.add_address(
            job_id=job_id,
            kind="dropoff",
            raw_text=raw_text,
        )

        await session.commit()

    await state.set_state(JobRequestStates.item_description)

    await message.answer(
        "Что нужно перевезти? Кратко опишите груз."
    )
