import html

from aiogram import F
from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery
from aiogram.types import Message

from app.domain.job_status import JobStatus
from app.db.session import async_session_maker
from app.repositories.carrier import CarrierRepository
from app.repositories.job import JobRepository
from app.services.job_offer import JobAlreadyAssignedError
from app.services.job_offer import JobOfferService
from app.services.job_offer import OfferAlreadyResolvedError
from app.services.job_offer import parse_offer_callback
from app.services.carrier_search import CarrierSearchService
from app.services.job_matching import JobMatchingService
from app.services.offer_distribution import OfferDistributionService
from app.services.job_escalation import escalate_job_to_manual_review
from app.services.offer_notification import send_job_offers_to_carriers

router = Router()



async def _delete_message_safely(message: Message) -> None:
    try:
        await message.delete()
    except TelegramBadRequest:
        await message.edit_reply_markup(reply_markup=None)


async def _delete_message_by_id_safely(bot, *, chat_id: int | None, message_id: int | None) -> None:
    if chat_id is None or message_id is None:
        return

    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramBadRequest:
        return


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
    sibling_offer_message_refs: list[tuple[int | None, int | None]] = []
    job = None

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
                accepted_offer = await offer_service.accept_offer_without_assignment(offer_id)
            except OfferAlreadyResolvedError:
                await callback.answer("Этот оффер уже обработан.", show_alert=True)
                await session.rollback()
                return
            except JobAlreadyAssignedError:
                await callback.answer("Заявка уже не принимает предложения.", show_alert=True)
                await session.rollback()
                return

            job = await job_repository.get_job_by_id(accepted_offer.job_id)
            message_text = (
                "Спасибо. Ваш отклик отправлен. "
                "Клиент получит предложения от перевозчиков и выберет подходящее."
            )
        else:
            declined_offer = await offer_service.decline_offer(offer_id)
            message_text = "Вы отказались от заказа."

            job = await job_repository.get_job_by_id(declined_offer.job_id)
            if job is not None and job.status == "offered":
                sibling_offers = await job_repository.list_offers_by_job(job.id)
                has_open_offer = any(
                    sibling.status in {"pending", "accepted"}
                    for sibling in sibling_offers
                )

                if not has_open_offer:
                    distribution = OfferDistributionService(
                        matching_service=JobMatchingService(
                            CarrierSearchService(carrier_repository)
                        ),
                        offer_service=offer_service,
                        job_repository=job_repository,
                    )
                    new_offers = await distribution.create_offers_for_job(
                        job,
                        limit=5,
                        expires_in_minutes=60,
                    )
                    if new_offers:
                        await send_job_offers_to_carriers(
                            bot=callback.bot,
                            job=job,
                            offers=new_offers,
                            job_repository=job_repository,
                            carrier_repository=carrier_repository,
                        )
                    else:
                        await escalate_job_to_manual_review(
                            bot=callback.bot,
                            job=job,
                            job_repository=job_repository,
                        )

        await session.commit()

    if callback.message:
        if action == "accept":
            await _finalize_offer_message(
                callback.message,
                message_text,
                reply_markup=None,
            )
        else:
            await _delete_message_safely(callback.message)

    for chat_id, message_id in sibling_offer_message_refs:
        await _delete_message_by_id_safely(
            callback.bot,
            chat_id=chat_id,
            message_id=message_id,
        )

    await callback.answer()
