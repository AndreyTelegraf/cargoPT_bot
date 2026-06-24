from aiogram import F
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.job_request_keyboards import support_keyboard
from app.bot.states.job_request import JobRequestStates
from app.db.session import async_session_maker
from app.repositories.job import JobRepository
from app.services.job import JobService

router = Router()


@router.message(JobRequestStates.pickup_address, F.text | F.location)
async def job_pickup_address(
    message: Message,
    state: FSMContext,
) -> None:
    raw_text = (message.text or "").strip()
    latitude = None
    longitude = None

    if message.location:
        latitude = message.location.latitude
        longitude = message.location.longitude
        raw_text = f"Telegram location: {latitude}, {longitude}"

    if not raw_text:
        await message.answer("Укажите адрес, ссылку на Google Maps или отправьте геолокацию Telegram.")
        return

    data = await state.get_data()
    job_id = data["job_id"]

    async with async_session_maker() as session:
        repository = JobRepository(session)
        service = JobService(repository)

        address = await service.add_address(
            job_id=job_id,
            kind="pickup",
            raw_text=raw_text,
            latitude=latitude,
            longitude=longitude,
        )

        await session.commit()

    await state.update_data(pickup_address_id=address.id)
    await state.set_state(JobRequestStates.pickup_details)

    await message.answer(
        "Этаж загрузки и лифт.\n\n"
        "Напишите в формате: этаж, лифт да/нет.\n"
        "Примеры: 2, да; 0, нет; -1, да",
        reply_markup=support_keyboard(),
    )
