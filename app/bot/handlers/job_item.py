from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.job_request import JobRequestStates
from app.db.session import async_session_maker
from app.repositories.job import JobRepository
from app.services.job import JobService

router = Router()


@router.message(JobRequestStates.item_description)
async def job_item_description(
    message: Message,
    state: FSMContext,
) -> None:
    description = (message.text or "").strip()

    if not description:
        await message.answer("Опишите груз коротким текстом.")
        return

    data = await state.get_data()
    job_id = data["job_id"]

    async with async_session_maker() as session:
        repository = JobRepository(session)
        service = JobService(repository)

        await service.add_item(
            job_id=job_id,
            description=description,
            quantity=None,
        )

        await session.commit()

    await state.set_state(JobRequestStates.estimated_payload_kg)

    await message.answer(
        "Примерный вес груза в кг? Если не знаете — напишите 0."
    )
