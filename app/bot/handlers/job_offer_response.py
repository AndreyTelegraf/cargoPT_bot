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


def _telegram_user_link(user_id: int | None, label: str) -> str:
    if not user_id:
        return "не указан"
    return f'<a href="tg://user?id={int(user_id)}">{_safe(label)}</a>'


def _build_client_notification_text(job, carrier) -> str:
    carrier_name = carrier.contact_name or carrier.company_name or "перевозчик"
    return (
        f"Перевозчик принял вашу заявку #{job.id}.\\n\\n"
        "Я познакомил вас с перевозчиком. Напишите ему в Telegram или по телефону, "
        "если нужно уточнить детали перевозки.\\n\\n"
        f"Компания: {_safe(carrier.company_name or 'не указана')}\\n"
        f"Контактное лицо: {_safe(carrier.contact_name or 'не указано')}\\n"
        f"Телефон: {_safe(carrier.phone or 'не указан')}\\n"
        f"Telegram: {_telegram_user_link(carrier.telegram_user_id, carrier_name)}"
    )


def _build_carrier_notification_text(job, carrier) -> str:
    client_label = job.client_telegram_username or "клиент"
    return (
        f"Вы приняли заказ #{job.id}.\\n\\n"
        "Я познакомил вас с клиентом. Напишите ему в Telegram или по телефону, "
        "если нужно уточнить детали перевозки.\\n\\n"
        f"Клиент: {_telegram_user_link(job.client_telegram_user_id, client_label)}\\n"
        f"Username: {_format_telegram_username(job.client_telegram_username)}\\n"
        f"Телефон: {_safe(job.client_phone or 'не указан')}\\n"
        f"WhatsApp: {_safe(job.client_whatsapp or 'не указан')}"
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
                    parse_mode="HTML",
                )
                message_text = _build_carrier_notification_text(job, carrier)
        else:
            await offer_service.decline_offer(offer_id)
            message_text = "Вы отказались от заказа."

        await session.commit()

    if callback.message:
        await callback.message.edit_text(message_text, parse_mode="HTML")

    await callback.answer()
