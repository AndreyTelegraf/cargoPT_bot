from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.job_request_keyboards import client_start_keyboard
from app.bot.job_request_keyboards import username_ready_keyboard
from app.bot.states.job_request import JobRequestStates
from app.db.session import async_session_maker
from app.repositories.job import JobRepository
from app.services.request_draft import ClientBannedError
from app.services.request_draft import RequestDraftService

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
        draft_service = RequestDraftService(job_repository=repository)

        try:
            result = await draft_service.create_or_reuse_telegram_draft(
                client_telegram_user_id=message.from_user.id,
                client_telegram_username=message.from_user.username,
            )
        except ClientBannedError:
            await message.answer(
                "Вы временно отключены от создания заявок CargoPT. "
                "По вопросам: https://t.me/andreytelegraf"
            )
            await session.rollback()
            return

        job = result.job
        await session.commit()

    await state.set_state(JobRequestStates.pickup_address)
    await state.update_data(job_id=job.id)

    await message.answer(
        "Начнём с места, где нужно забрать ваш груз.\n\n"
        "Вставьте ссылку на локацию из Google Maps или введите его адрес текстом в формате "
        "\"улица, номер дома, город и почтовый индекс\", например Rua dos Contrabandistas, 1, Lisboa, 1350-085",
        reply_markup=client_start_keyboard(),
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
