import re
from datetime import UTC
from datetime import datetime

from aiogram import F
from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from app.bot.assignment_confirmation_keyboard import build_assignment_failure_reason_keyboard
from app.bot.carrier_locale import normalize_carrier_locale
from app.bot.offer_locale import offer_text as t
from app.db.session import async_session_maker
from app.domain.job_decline_reason import is_valid_decline_reason
from app.domain.job_status import JobStatus
from app.repositories.carrier import CarrierRepository
from app.repositories.job import JobRepository
from app.services.assignment_confirmation import build_assignment_cleanup_target
from app.services.assignment_confirmation import build_assignment_result_text
from app.services.assignment_confirmation import build_assignment_status_from_action
from app.services.assignment_confirmation import format_telegram_status_block
from app.services.assignment_confirmation import parse_assignment_callback
from app.services.assignment_confirmation import process_assignment_failure_redispatch
from app.services.assignment_confirmation import record_assignment_confirmation
from app.services.assignment_confirmation import resolve_assignment_actor
from app.services.assignment_notifications import send_assignment_final_notifications
from app.services.job_lifecycle import InvalidJobStatusTransitionError

router = Router()


async def _delete_message_by_id_safely(bot, *, chat_id: int | None, message_id: int | None) -> None:
    if chat_id is None or message_id is None:
        return

    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramBadRequest:
        return


def _build_assignment_confirmation_final_text(message, status_text: str) -> str:
    original_text = message.text or message.caption or ""
    original_text = original_text.strip()

    if original_text:
        return f"{original_text}\n\n{status_text}"

    return status_text


@router.callback_query(F.data.startswith("assignment:"))
async def handle_assignment_confirmation(callback: CallbackQuery) -> None:
    raw_data = callback.data or ""
    failure_reason = None
    locale = normalize_carrier_locale(callback.from_user.language_code)

    if raw_data.startswith("assignment:fail_reason:"):
        parts = raw_data.split(":")
        if len(parts) != 4:
            await callback.answer(t(locale, "invalid_button"), show_alert=True)
            return

        try:
            job_id = int(parts[2])
        except ValueError:
            await callback.answer(t(locale, "invalid_button"), show_alert=True)
            return

        failure_reason = parts[3]
        if not is_valid_decline_reason(failure_reason):
            await callback.answer(t(locale, "invalid_reason"), show_alert=True)
            return

        action = "fail"
    else:
        try:
            action, job_id = parse_assignment_callback(raw_data)
        except ValueError:
            await callback.answer(t(locale, "invalid_button"), show_alert=True)
            return

    if action == "fail" and failure_reason is None:
        async with async_session_maker() as locale_session:
            locale_carrier = await CarrierRepository(
                locale_session
            ).get_carrier_by_telegram_user_id(callback.from_user.id)
            if locale_carrier is not None:
                locale = normalize_carrier_locale(
                    locale_carrier.preferred_locale or locale
                )
        if callback.message:
            await callback.message.edit_text(
                t(locale, "assignment_failure_reason_prompt"),
                reply_markup=build_assignment_failure_reason_keyboard(
                    job_id,
                    locale=locale,
                ),
            )
        await callback.answer()
        return

    telegram_user_id = callback.from_user.id

    async with async_session_maker() as session:
        job_repository = JobRepository(session)
        carrier_repository = CarrierRepository(session)
        job = await job_repository.get_job_by_id(job_id)
        accepted_offer = await job_repository.get_accepted_offer_by_job_id(job_id)
        locale_carrier = await carrier_repository.get_carrier_by_telegram_user_id(
            telegram_user_id
        )
        if locale_carrier is not None:
            locale = normalize_carrier_locale(
                locale_carrier.preferred_locale or locale
            )

        if job is None:
            await callback.answer(t(locale, "job_not_found"), show_alert=True)
            return

        if failure_reason is not None and accepted_offer is None:
            await callback.answer(t(locale, "offer_not_found"), show_alert=True)
            return

        actor = await resolve_assignment_actor(
            telegram_user_id=telegram_user_id,
            job=job,
            accepted_offer=accepted_offer,
            carrier_repository=carrier_repository,
        )

        if actor is None:
            await callback.answer(t(locale, "not_your_button"), show_alert=True)
            return

        if action == "fail" and actor == "client" and job.status == JobStatus.ASSIGNED:
            now = datetime.now(UTC)
            accepted_offer = await job_repository.cancel_accepted_offer_by_job(
                job_id=job_id,
                cancelled_at=now,
            )
            await job_repository.clear_assignment_confirmation_statuses(
                job_id=job_id,
                updated_at=now,
            )
            updated_job = await job_repository.update_job_status(
                job_id=job_id,
                status=JobStatus.READY_FOR_MATCHING,
                updated_at=now,
            )
            result_text = build_assignment_result_text(
                job_id=job_id,
                action=action,
                job_status=updated_job.status,
                locale=locale,
                actor=actor,
            )
        else:
            if job.status != JobStatus.ASSIGNED_PENDING_CONFIRMATION:
                await callback.answer(t(locale, "job_status_changed"), show_alert=True)
                return

            confirmation_status = build_assignment_status_from_action(action)

            if failure_reason is not None:
                accepted_offer.decline_reason = failure_reason

            try:
                updated_job = await record_assignment_confirmation(
                    job_repository,
                    job_id=job_id,
                    actor=actor,
                    status=confirmation_status,
                )
                result_text = build_assignment_result_text(
                    job_id=job_id,
                    action=action,
                    job_status=updated_job.status,
                    locale=locale,
                    actor=actor,
                )
            except InvalidJobStatusTransitionError:
                await session.rollback()
                await callback.answer(t(locale, "job_status_changed"), show_alert=True)
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

        if updated_job.status == JobStatus.MANUAL_REVIEW_REQUIRED:
            result_text = build_assignment_result_text(
                job_id=job_id,
                action=action,
                job_status=updated_job.status,
                locale=locale,
                actor=actor,
            )

        await send_assignment_final_notifications(
            bot=callback.bot,
            job=updated_job,
            accepted_offer=accepted_offer,
            carrier_repository=carrier_repository,
        )

        await session.commit()

    if should_delete_carrier_offer:
        await _delete_message_by_id_safely(
            callback.bot,
            chat_id=carrier_message_chat_id,
            message_id=carrier_message_id,
        )

    alert_text = re.sub(r"<[^>]+>", "", result_text)

    if callback.message:
        try:
            await callback.message.edit_text(
                _build_assignment_confirmation_final_text(
                    callback.message,
                    result_text,
                ),
                parse_mode="HTML",
                reply_markup=None,
            )
        except TelegramBadRequest:
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except TelegramBadRequest:
                pass

    await callback.answer(alert_text, show_alert=True)
