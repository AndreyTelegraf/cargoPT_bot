import html

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto
from aiogram.types import InputMediaVideo
from aiogram.types import Message
from aiogram.types import ReplyKeyboardRemove
from app.bot.offer_keyboard import build_offer_keyboard

from app.bot.states.job_request import JobRequestStates
from app.db.session import async_session_maker
from app.repositories.job import JobRepository
from app.services.job import JobService
from app.repositories.carrier import CarrierRepository
from app.services.carrier_search import CarrierSearchService
from app.services.job_matching import JobMatchingService
from app.services.job_offer import JobOfferService
from app.services.offer_distribution import OfferDistributionService

router = Router()


def _safe(value) -> str:
    return html.escape(str(value), quote=False)


def _format_address(label: str, raw_text: str | None, map_url: str | None) -> str:
    value = _safe(raw_text or "не указан")
    safe_label = _safe(label)
    if map_url and map_url != raw_text:
        return f"<b>{safe_label}</b>\n{value}\nКарта: {_safe(map_url)}"
    return f"<b>{safe_label}</b>\n{value}"


def _format_requested_date(value) -> str:
    if value is None:
        return "<b>Дата и время</b>\nне указаны"
    return "<b>Дата и время</b>\n" + _safe(value.strftime("%d.%m.%Y %H:%M"))


def _format_bool(value: bool) -> str:
    return "да" if value else "нет"


def _format_value(value, suffix: str) -> str:
    if value is None:
        return "не указано"
    return _safe(f"{value}{suffix}")


def _format_items(items) -> str:
    descriptions = [_safe(item.description) for item in items if item.description]
    return "; ".join(descriptions) if descriptions else "не указан"


def _build_offer_text(job, items, pickup, dropoff) -> str:
    return (
        f"<b>Новая заявка #{job.id}</b>\n\n"
        f"{_format_requested_date(job.requested_date)}\n\n"
        f"{_format_address('Откуда', pickup.raw_text if pickup else None, pickup.map_url if pickup else None)}\n\n"
        f"{_format_address('Куда', dropoff.raw_text if dropoff else None, dropoff.map_url if dropoff else None)}\n\n"
        "<b>Груз</b>\n"
        f"{_format_items(items)}\n\n"
        "<b>Параметры</b>\n"
        f"Вес: {_format_value(job.estimated_payload_kg, ' кг')}\n"
        f"Объём: {_format_value(job.estimated_volume_m3, ' м³')}\n"
        f"Грузчики: {_format_value(job.required_loaders, '')}\n"
        f"Гидроборт: {_format_bool(job.needs_tail_lift)}\n"
        f"Кран: {_format_bool(job.needs_crane)}\n"
        f"Подъём через окно: {_format_bool(job.needs_mobile_lift)}\n\n"
        "<b>Комментарий</b>\n"
        f"{_safe(job.comment or 'нет')}\n\n"
        "<b>Контакты клиента</b>\n"
        f"Telegram: @{_safe(job.client_telegram_username or 'username_missing')}\n"
        f"Телефон: {_safe(job.client_phone or 'не указан')}\n"
        f"WhatsApp: {_safe(job.client_whatsapp or 'не указан')}\n\n"
        "Примите или отклоните заявку."
    )


@router.message(JobRequestStates.comment)
async def job_comment(
    message: Message,
    state: FSMContext,
) -> None:
    raw_comment = (message.text or "").strip()
    comment = None if raw_comment in {"", "-", "Без комментария"} else raw_comment

    data = await state.get_data()
    job_id = data["job_id"]

    async with async_session_maker() as session:
        job_repository = JobRepository(session)
        carrier_repository = CarrierRepository(session)
        job_service = JobService(job_repository)

        job = await job_service.finalize_for_matching(
            job_id=job_id,
            comment=comment,
        )

        distribution = OfferDistributionService(
            matching_service=JobMatchingService(
                CarrierSearchService(carrier_repository)
            ),
            offer_service=JobOfferService(job_repository),
            job_repository=job_repository,
        )

        offers = await distribution.create_offers_for_job(
            job,
            limit=5,
            expires_in_minutes=60,
        )

        media_items = await job_repository.list_media_by_job(job.id)
        items = await job_repository.list_items_by_job(job.id)
        addresses = await job_repository.list_addresses_by_job(job.id)
        pickup = next((item for item in addresses if item.kind == "pickup"), None)
        dropoff = next((item for item in addresses if item.kind == "dropoff"), None)

        sent_count = 0

        for offer in offers:
            carrier = await carrier_repository.get_carrier_by_vehicle_id(
                offer.vehicle_id
            )

            if carrier is None or carrier.telegram_user_id is None:
                continue

            offer_text = _build_offer_text(job, items, pickup, dropoff)
            keyboard = build_offer_keyboard(offer.id)

            if not media_items:
                await message.bot.send_message(
                    chat_id=carrier.telegram_user_id,
                    text=offer_text,
                    reply_markup=keyboard,
                )
            elif len(media_items) == 1:
                media = media_items[0]
                if media.media_type == "photo":
                    await message.bot.send_photo(
                        chat_id=carrier.telegram_user_id,
                        photo=media.telegram_file_id,
                        caption=offer_text,
                        reply_markup=keyboard,
                    )
                elif media.media_type == "video":
                    await message.bot.send_video(
                        chat_id=carrier.telegram_user_id,
                        video=media.telegram_file_id,
                        caption=offer_text,
                        reply_markup=keyboard,
                    )
                else:
                    await message.bot.send_message(
                        chat_id=carrier.telegram_user_id,
                        text=offer_text,
                        reply_markup=keyboard,
                    )
            else:
                album = []
                for index, media in enumerate(media_items[:10]):
                    caption = offer_text if index == 0 else None
                    if media.media_type == "photo":
                        album.append(InputMediaPhoto(media=media.telegram_file_id, caption=caption, parse_mode="HTML"))
                    elif media.media_type == "video":
                        album.append(InputMediaVideo(media=media.telegram_file_id, caption=caption, parse_mode="HTML"))

                if album:
                    await message.bot.send_media_group(
                        chat_id=carrier.telegram_user_id,
                        media=album,
                    )

                await message.bot.send_message(
                    chat_id=carrier.telegram_user_id,
                    text=f"Решение по заявке #{job.id}",
                    reply_markup=keyboard,
                )

            sent_count += 1

        await session.commit()

    await state.clear()

    await message.answer(
        f"Заявка готова. Мы отправили её подходящим перевозчикам: {sent_count}.\n"
        "Когда кто-то примет заказ, вы получите уведомление здесь.",
        reply_markup=ReplyKeyboardRemove(),
    )
