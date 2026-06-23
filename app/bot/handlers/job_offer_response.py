from aiogram import F
from aiogram import Router
from aiogram.types import CallbackQuery

from app.db.session import async_session_maker
from app.repositories.carrier import CarrierRepository
from app.repositories.job import JobRepository
from app.services.job_offer import JobOfferService

router = Router()


def _parse_offer_callback(data: str) -> tuple[str, int]:
    parts = data.split(":")
    if len(parts) != 3 or parts[0] != "offer":
        raise ValueError("invalid callback data")

    action = parts[1]
    offer_id = int(parts[2])

    if action not in {"accept", "decline"}:
        raise ValueError("invalid offer action")

    return action, offer_id


@router.callback_query(F.data.startswith("offer:"))
async def handle_offer_response(callback: CallbackQuery) -> None:
    try:
        action, offer_id = _parse_offer_callback(callback.data or "")
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
            accepted_offer = await offer_service.accept_offer_and_assign_job(offer_id)
            job = await job_repository.get_job_by_id(accepted_offer.job_id)
            message_text = "Заявка принята и закреплена за вами."

            if job is not None:
                await callback.bot.send_message(
                    chat_id=job.client_telegram_user_id,
                    text=(
                        "Перевозчик принял вашу заявку.\n"
                        f"Заявка #{job.id}.\n"
                        "Мы свяжем вас с перевозчиком на следующем шаге."
                    ),
                )
                await callback.bot.send_message(
                    chat_id=telegram_user_id,
                    text=(
                        f"Вы приняли заявку #{job.id}.\n"
                        f"Клиент: @{job.client_telegram_username or 'username_missing'}\n"
                        f"Телефон: {job.client_phone or 'не указан'}\n"
                        f"WhatsApp: {job.client_whatsapp or 'не указан'}"
                    ),
                )
        else:
            await offer_service.decline_offer(offer_id)
            message_text = "Вы отказались от заказа."

        await session.commit()

    if callback.message:
        if callback.message.text:
            await callback.message.edit_text(message_text)
        elif callback.message.caption:
            await callback.message.edit_caption(caption=message_text)
        else:
            await callback.bot.send_message(chat_id=telegram_user_id, text=message_text)

    await callback.answer()
