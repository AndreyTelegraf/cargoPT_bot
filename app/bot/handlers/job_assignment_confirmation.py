from aiogram import F
from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from app.db.session import async_session_maker
from app.repositories.carrier import CarrierRepository
from app.repositories.job import JobRepository
from app.services.assignment_resolution import process_assignment_decision
from app.services.job import InvalidJobStatusTransitionError
from app.services.job import JobService

router = Router()


async def _delete_message_by_id_safely(bot, *, chat_id: int | None, message_id: int | None) -> None:
    if chat_id is None or message_id is None:
        return

    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramBadRequest:
        return


def _parse_assignment_callback(data: str) -> tuple[str, int]:
    parts = data.split(":")
    if len(parts) != 3 or parts[0] != "assignment":
        raise ValueError("invalid callback data")

    action = parts[1]
    job_id = int(parts[2])

    if action not in {"confirm", "fail"}:
        raise ValueError("invalid assignment action")

    return action, job_id


@router.callback_query(F.data.startswith("assignment:"))
async def handle_assignment_confirmation(callback: CallbackQuery) -> None:
    try:
        action, job_id = _parse_assignment_callback(callback.data or "")
    except ValueError:
        await callback.answer("Некорректная кнопка", show_alert=True)
        return

    telegram_user_id = callback.from_user.id

    async with async_session_maker() as session:
        job_repository = JobRepository(session)
        carrier_repository = CarrierRepository(session)
        job_service = JobService(job_repository)

        try:
            result = await process_assignment_decision(
                bot=callback.bot,
                telegram_user_id=telegram_user_id,
                job_id=job_id,
                action=action,
                job_repository=job_repository,
                carrier_repository=carrier_repository,
                job_service=job_service,
            )
        except InvalidJobStatusTransitionError:
            await session.rollback()
            await callback.answer("Статус заявки уже изменён.", show_alert=True)
            return

        if result is None:
            await callback.answer("Эта кнопка не для вас.", show_alert=True)
            return

        await session.commit()

    if result.should_delete_carrier_offer:
        await _delete_message_by_id_safely(
            callback.bot,
            chat_id=result.carrier_message_chat_id,
            message_id=result.carrier_message_id,
        )

    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)

    await callback.answer(result.message, show_alert=True)
