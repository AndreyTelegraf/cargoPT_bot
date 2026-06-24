import html

from aiogram import F
from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery
from aiogram.types import Message

from app.bot.assignment_confirmation_keyboard import build_assignment_confirmation_keyboard
from app.db.session import async_session_maker
from app.repositories.carrier import CarrierRepository
from app.repositories.job import JobRepository
from app.services.job_offer import JobAlreadyAssignedError
from app.services.job_offer import JobOfferService
from app.services.job_offer import OfferAlreadyResolvedError
from app.services.job_offer import parse_offer_callback
from app.services.offer_notifications import build_client_notification_text
from app.services.offer_notifications import build_carrier_notification_text

router = Router()



async def _delete_message_safely(message: Message) -> None:
    try:
        await message.delete()
    except TelegramBadRequest:
        await message.edit_reply_markup(reply_markup=None)


async def _finalize_offer_message(message: Message, text: str, reply_markup=None) -> None:
    if message.text is not None:
        await message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
        return

    if message.caption is not None:
        await message.edit_caption(caption=text, parse_mode="HTML", reply_markup=reply_markup)
        return

    await message.edit_reply_markup(reply_markup=reply_markup)

@router.callback_query(F.data.startswith("offer:"))
async def handle_offer_response(callback: CallbackQuery) -> None:
    try:
        action, offer_id = parse_offer_callback(callback.data or "")
    except ValueError:
        await callback.answer("Некорректная кнопка", show_alert=True)
        return

    telegram_user_id = callback.from_user.id

    async with async_session_maker() as session:
        carrier_repository = CarrierRepository(session)
        job_repository = JobRepository(session)
        offer_service = JobOfferService(job_repository)

        carrier = await carrier_repository.get_carrier_by_telegram_user_id(
            telegram_user_id
        )

        offer = await job_repository.get_offer_by_id(offer_id)

        if carrier is None or offer is None or offer.carrier_id != carrier.id:
            await callback.answer("Оффер не найден", show_alert=True)
            return

        if action == "accept":
            try:
                accepted_offer = await offer_service.accept_offer_and_assign_job(offer_id)
            except OfferAlreadyResolvedError:
                await callback.answer("Этот оффер уже обработан.", show_alert=True)
                await session.rollback()
                return
            except JobAlreadyAssignedError:
                await callback.answer("Заказ уже закреплён за другим перевозчиком.", show_alert=True)
                await session.rollback()
                return

            job = await job_repository.get_job_by_id(accepted_offer.job_id)
            message_text = "Вы приняли заказ. Мы закрепили заявку за вами."

            if job is not None:
                confirmation_keyboard = build_assignment_confirmation_keyboard(job.id)
                await callback.bot.send_message(
                    chat_id=job.client_telegram_user_id,
                    text=build_client_notification_text(job, carrier),
                    parse_mode="HTML",
                    reply_markup=confirmation_keyboard,
                )
                message_text = build_carrier_notification_text(job, carrier)
        else:
            await offer_service.decline_offer(offer_id)
            message_text = "Вы отказались от заказа."

        await session.commit()

    if callback.message:
        if action == "accept" and job is not None:
            await _finalize_offer_message(
                callback.message,
                message_text,
                reply_markup=build_assignment_confirmation_keyboard(job.id),
            )
        else:
            await _delete_message_safely(callback.message)

    await callback.answer()
