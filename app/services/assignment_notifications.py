from app.domain.job_status import JobStatus
from app.bot.assignment_confirmation_keyboard import build_assignment_confirmation_keyboard
from app.bot.offer_locale import offer_text as t
from app.repositories.carrier import CarrierRepository
from app.services.assignment_confirmation import format_telegram_status_block


def build_carrier_assignment_confirmation_text(
    job,
    locale: str | None = None,
) -> str:
    import html

    client_link = (
        f'<a href="tg://user?id={int(job.client_telegram_user_id)}">'
        f'{html.escape(job.client_telegram_username or t(locale, "client"), quote=False)}</a>'
        if job.client_telegram_user_id is not None
        and job.client_telegram_username
        else html.escape(job.customer_name or "S/N", quote=False)
    )
    username = (
        "@" + html.escape(job.client_telegram_username.lstrip("@"), quote=False)
        if job.client_telegram_username
        else "S/N"
    )

    return (
        f"{t(locale, 'assignment_selected', job_id=job.id)}\n\n"
        f"{t(locale, 'client')}: {client_link}\n"
        f"{t(locale, 'username')}: {username}\n"
        f"{t(locale, 'phone')}: {html.escape(job.client_phone or t(locale, 'not_provided'), quote=False)}\n"
        f"WhatsApp: {html.escape(job.client_whatsapp or t(locale, 'not_provided'), quote=False)}\n\n"
        f"{t(locale, 'contact_customer')}"
    )


async def send_assignment_confirmation_requests(
    *,
    bot,
    job,
    carrier_telegram_user_id: int | None,
    carrier_locale: str | None = None,
) -> None:
    if carrier_telegram_user_id is not None:
        await bot.send_message(
            chat_id=carrier_telegram_user_id,
            text=build_carrier_assignment_confirmation_text(
                job,
                locale=carrier_locale,
            ),
            reply_markup=build_assignment_confirmation_keyboard(
                job.id,
                locale=carrier_locale,
            ),
            parse_mode="HTML",
        )


async def send_assignment_final_notifications(
    *,
    bot,
    job,
    accepted_offer,
    carrier_repository: CarrierRepository,
) -> None:
    if job.status not in {
        JobStatus.ASSIGNED,
        JobStatus.READY_FOR_MATCHING,
        JobStatus.MANUAL_REVIEW_REQUIRED,
    }:
        return

    carrier = None
    if accepted_offer is not None:
        carrier = await carrier_repository.get_carrier_by_id(
            accepted_offer.carrier_id
        )

    if job.status == JobStatus.ASSIGNED:
        client_text = format_telegram_status_block(
            (
                f"Сделка по заявке №{job.id} подтверждена обеими сторонами.\n\n"
                "Свяжитесь с перевозчиком напрямую и согласуйте последние детали перевозки."
            ),
            state="success",
        )
        carrier_text = format_telegram_status_block(
            (
                f"Сделка по заявке №{job.id} подтверждена обеими сторонами.\n\n"
                "Свяжитесь с клиентом напрямую и согласуйте последние детали перевозки."
            ),
            state="success",
        )
    elif job.status == JobStatus.READY_FOR_MATCHING:
        client_text = format_telegram_status_block(
            (
                f"По заявке №{job.id} договориться с перевозчиком не удалось.\n\n"
                "Заявка снова в поиске. "
                "Мы отправляем её другим подходящим перевозчикам."
            ),
            state="searching",
        )
        carrier_text = format_telegram_status_block(
            (
                f"По заявке №{job.id} договориться с клиентом не удалось.\n\n"
                "Для вас эта заявка закрыта."
            ),
            state="failed",
        )
    else:
        client_text = format_telegram_status_block(
            (
                f"По заявке №{job.id} договориться с перевозчиком не удалось.\n\n"
                "До перевозки осталось меньше трёх суток, поэтому "
                "автоматическая рассылка остановлена. "
                "Заявку проверит диспетчер CargoPT."
            ),
            state="searching",
        )
        carrier_text = format_telegram_status_block(
            (
                f"По заявке №{job.id} договориться с клиентом не удалось.\n\n"
                "Для вас эта заявка закрыта."
            ),
            state="failed",
        )

    if job.client_telegram_user_id is not None:
        await bot.send_message(
            chat_id=job.client_telegram_user_id,
            text=client_text,
            parse_mode="HTML",
        )

    if carrier is not None and carrier.telegram_user_id is not None:
        await bot.send_message(
            chat_id=carrier.telegram_user_id,
            text=carrier_text,
            parse_mode="HTML",
        )
