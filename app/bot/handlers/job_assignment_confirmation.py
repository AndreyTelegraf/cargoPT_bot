from aiogram import F
from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from app.db.session import async_session_maker
from app.domain.job_status import JobStatus
from app.repositories.job import JobRepository
from app.services.assignment_confirmation import build_assignment_cleanup_target
from app.services.assignment_confirmation import build_assignment_result_text
from app.services.assignment_confirmation import build_assignment_status_from_action
from app.services.assignment_confirmation import parse_assignment_callback
from app.services.assignment_confirmation import process_assignment_failure_redispatch
from app.services.assignment_confirmation import record_assignment_confirmation
from app.services.assignment_confirmation import resolve_assignment_actor
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


@router.callback_query(F.data.startswith("assignment:"))
async def handle_assignment_confirmation(callback: CallbackQuery) -> None:
    try:
        action, job_id = parse_assignment_callback(callback.data or "")
    except ValueError:
        await callback.answer("Некорректная кнопка", show_alert=True)
        return

    telegram_user_id = callback.from_user.id

    async with async_session_maker() as session:
        job_repository = JobRepository(session)
        carrier_repository = CarrierRepository(session)
        job_service = JobService(job_repository)

        job = await job_repository.get_job_by_id(job_id)
        accepted_offer = await job_repository.get_accepted_offer_by_job_id(job_id)

        if job is None:
            await callback.answer("Заявка не найдена.", show_alert=True)
            return

        actor = await resolve_assignment_actor(
            telegram_user_id=telegram_user_id,
            job=job,
            accepted_offer=accepted_offer,
            carrier_repository=carrier_repository,
        )

        if actor is None:
            await callback.answer("Эта кнопка не для вас.", show_alert=True)
            return

        if job.status != JobStatus.ASSIGNED_PENDING_CONFIRMATION:
            await callback.answer("Статус заявки уже изменён.", show_alert=True)
            return

        confirmation_status = build_assignment_status_from_action(action)

        try:
            updated_job = await record_assignment_confirmation(
                job_service,
                job_id=job_id,
                actor=actor,
                status=confirmation_status,
            )
            result_text = build_assignment_result_text(
                job_id=job_id,
                action=action,
                job_status=updated_job.status,
            )
        except InvalidJobStatusTransitionError:
            await session.rollback()
            await callback.answer("Статус заявки уже изменён.", show_alert=True)
            return

        (
            should_delete_carrier_offer,
            carrier_message_chat_id,
            carrier_message_id,
        ) = await process_assignment_failure_redispatch(
            bot=callback.bot,
            job=updated_job,
            accepted_offer=accepted_offer,
            job_repository=job_repository,
            carrier_repository=carrier_repository,
        )

        await session.commit()

    if should_delete_carrier_offer:
        await _delete_message_by_id_safely(
            callback.bot,
            chat_id=carrier_message_chat_id,
            message_id=carrier_message_id,
        )

    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)

    await callback.answer(result_text, show_alert=True)
