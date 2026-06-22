from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.job_request_keyboards import volume_keyboard

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

    payload_map = {
        "до 500 кг": 500,
        "до 1000 кг": 1000,
        "до 1600 кг": 1600,
        "до 3500 кг": 3500,
        "Не знаю": 0,
    }

    if raw_value in payload_map:
        value = payload_map[raw_value]
    else:
        try:
            value = int(raw_value)
        except ValueError:
            await message.answer("Выберите вариант кнопкой или укажите вес числом в кг.")
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
        "Оцените примерный объём груза.\n\n"
        "Ориентир по машине:\n"
        "- до 3 м³ — несколько вещей или коробок;\n"
        "- до 10 м³ — маленький фургон;\n"
        "- до 18 м³ — большой фургон;\n"
        "- до 35 м³ — грузовик.\n\n"
        "Можно нажать кнопку или ввести число в м³.",
        reply_markup=volume_keyboard(),
    )
