import html

from aiogram import F
from aiogram import Router
from aiogram.types import CallbackQuery

from app.db.session import async_session_maker
from app.repositories.carrier import CarrierRepository
from app.repositories.job import JobRepository
from app.services.job_offer import JobOfferService

router = Router()


def _safe(value) -> str:
    return html.escape(str(value), quote=False)


def _format_contact_line(label: str, value) -> str:
    return f"{label}: {_safe(value or 'не указан')}"


def _format_telegram_username(username: str | None) -> str:
    if not username:
        return "не указан"
    return "@" + _safe(username.lstrip("@"))


def _build_client_notification_text(job, carrier) -> str:
    return (
        f"Перевозчик принял вашу заявку #{job.id}.\\n\\n"
        "Контакты перевозчика:\\n"
        f"{_format_contact_line('Компания', carrier.company_name)}\\n"
        f"{_format_contact_line('Контактное имя', carrier.contact_name)}\\n"
        f"{_format_contact_line('Телефон', carrier.phone)}\\n"
        f"Telegram: {_safe(carrier.telegram_user_id or 'не указан')}"
    )


def _build_carrier_notification_text(job) -> str:
    return (
        f"Вы приняли заказ #{job.id}.\\n\\n"
        "Контакты клиента:\\n"
        f"Telegram: {_format_telegram_username(job.client_telegram_username)}\\n"
        f"{_format_contact_line('Телефон', job.client_phone)}\\n"
        f"{_format_contact_line('WhatsApp', job.client_whatsapp)}"
    )


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
            message_text = "Вы приняли заказ. Мы закрепили заявку за вами."

            if job is not None:
                await callback.bot.send_message(
                    chat_id=job.client_telegram_user_id,
                    text=_build_client_notification_text(job, carrier),
                )
                message_text = _build_carrier_notification_text(job)
        else:
            await offer_service.decline_offer(offer_id)
            message_text = "Вы отказались от заказа."

        await session.commit()

    if callback.message:
        await callback.message.edit_text(message_text)

    await callback.answer()
