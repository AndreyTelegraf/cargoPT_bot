from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.job_request_keyboards import username_ready_keyboard
from app.bot.states.job_request import JobRequestStates
from app.db.session import async_session_maker
from app.repositories.job import JobRepository
from app.services.job import JobService

router = Router()


USERNAME_TEXT = (
    "Перед созданием заявки нужен Telegram username.\n\n"
    "Он нужен, чтобы перевозчик мог связаться с вами после принятия заказа, "
    "а бот мог показать контакт без ручного копирования телефона.\n\n"
    "Как создать username:\n"
    "1. Откройте Telegram Settings / Настройки.\n"
    "2. Нажмите Username / Имя пользователя.\n"
    "3. Придумайте имя латиницей, например cargo_client_123.\n"
    "4. Вернитесь сюда и нажмите «Готово, username создан»."
)


async def _create_job_and_ask_pickup(
    message: Message,
    state: FSMContext,
) -> None:
    async with async_session_maker() as session:
        repository = JobRepository(session)
        service = JobService(repository)

        job = await service.create_draft_job(
            client_telegram_user_id=message.from_user.id,
            client_telegram_username=message.from_user.username,
        )

        await session.commit()

    await state.set_state(JobRequestStates.pickup_address)
    await state.update_data(job_id=job.id)

    await message.answer(
        "Начнём с места погрузки.\n\n"
        "Пришлите адрес текстом или ссылку на точку в Google Maps.\n"
        "Лучше всего: улица, номер дома, город и почтовый индекс.\n"
        "Если есть сложный подъезд, шлагбаум или платная парковка — укажите это сразу."
    )


@router.message(Command("new_job"))
async def start_job_request(
    message: Message,
    state: FSMContext,
) -> None:
    if not message.from_user.username:
        await state.set_state(JobRequestStates.telegram_username_missing)
        await message.answer(
            USERNAME_TEXT,
            reply_markup=username_ready_keyboard(),
        )
        return

    await _create_job_and_ask_pickup(message, state)


@router.message(JobRequestStates.telegram_username_missing)
async def continue_after_username_created(
    message: Message,
    state: FSMContext,
) -> None:
    if not message.from_user.username:
        await message.answer(
            USERNAME_TEXT,
            reply_markup=username_ready_keyboard(),
        )
        return

    await _create_job_and_ask_pickup(message, state)
