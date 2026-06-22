from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.job_request_keyboards import whatsapp_keyboard
from app.bot.states.job_request import JobRequestStates
from app.db.session import async_session_maker
from app.repositories.job import JobRepository
from app.services.job import JobService

router = Router()


@router.message(JobRequestStates.contact_phone)
async def job_contact_phone(
    message: Message,
    state: FSMContext,
) -> None:
    raw_phone = (message.text or "").strip()
    phone = None if raw_phone in {"", "-", "Не указывать телефон"} else raw_phone

    data = await state.get_data()
    job_id = data["job_id"]

    async with async_session_maker() as session:
        repository = JobRepository(session)
        service = JobService(repository)

        await service.update_client_phone(
            job_id=job_id,
            client_phone=phone,
        )

        await session.commit()

    await state.update_data(client_phone=phone)
    await state.set_state(JobRequestStates.contact_whatsapp)

    await message.answer(
        "WhatsApp для связи.\n\n"
        "Если WhatsApp совпадает с основным телефоном — нажмите «WhatsApp совпадает».\n"
        "Если хотите дать другой номер — отправьте его сообщением.\n"
        "Если WhatsApp указывать не нужно — нажмите «Не указывать WhatsApp».",
        reply_markup=whatsapp_keyboard(),
    )
