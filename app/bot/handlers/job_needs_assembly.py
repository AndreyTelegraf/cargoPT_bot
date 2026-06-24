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


@router.message(JobRequestStates.needs_assembly, F.text.in_(["Да", "Нет"]))
async def job_needs_assembly(
    message: Message,
    state: FSMContext,
) -> None:
    needs_assembly = message.text == "Да"

    data = await state.get_data()
    job_id = data["job_id"]

    async with async_session_maker() as session:
        repository = JobRepository(session)
        service = JobService(repository)

        await service.update_needs_assembly(
            job_id=job_id,
            needs_assembly=needs_assembly,
        )

        await session.commit()

    await state.set_state(JobRequestStates.needs_packing)

    await message.answer(
        "Нужна ли упаковка или распаковка груза?\n\n"
        "Например: коробки, плёнка, защита мебели, упаковка техники или распаковка после доставки.",
        reply_markup=yes_no_keyboard(),
    )
