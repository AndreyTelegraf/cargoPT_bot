from aiogram import F
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.job_request_keyboards import yes_no_keyboard

from app.bot.states.job_request import JobRequestStates
from app.db.session import async_session_maker
from app.repositories.job import JobRepository
from app.services.request_update import RequestUpdateService

router = Router()


@router.message(JobRequestStates.needs_crane, F.text.in_(["Да", "Нет"]))
async def job_needs_crane(
    message: Message,
    state: FSMContext,
) -> None:
    needs_crane = message.text == "Да"

    data = await state.get_data()
    job_id = data["job_id"]

    async with async_session_maker() as session:
        repository = JobRepository(session)
        service = RequestUpdateService(job_repository=repository)

        await service.update_needs_crane(
            job_id=job_id,
            needs_crane=needs_crane,
        )

        await session.commit()

    await state.set_state(JobRequestStates.needs_mobile_lift)

    await message.answer(
        "Нужен ли подъём через окно или балкон?\n\n"
        "Это нужно, если груз не проходит в лифт, подъезд или по лестнице. Например: большой диван, шкаф, техника, стекло, тяжёлая мебель.",
        reply_markup=yes_no_keyboard(),
    )
