from app.bot.handlers.carrier_invite_admin import ADMIN_TELEGRAM_USER_IDS
from app.domain.job_status import JobStatus


def build_offer_escalation_text(*, job, offers) -> str:
    pending = sum(1 for offer in offers if offer.status == "pending")
    declined = sum(1 for offer in offers if offer.status == "declined")
    expired = sum(1 for offer in offers if offer.status == "expired")
    accepted = sum(1 for offer in offers if offer.status == "accepted")
    client = job.client_telegram_username or str(job.client_telegram_user_id)

    return (
        f"Заявка #{job.id} требует ручного контроля.\n\n"
        f"Клиент: @{client}\n"
        f"Статус: {job.status}\n\n"
        f"Офферы:\n"
        f"отправлено — {len(offers)}\n"
        f"pending — {pending}\n"
        f"accepted — {accepted}\n"
        f"declined — {declined}\n"
        f"expired — {expired}"
    )


async def notify_admins_about_unassigned_job(*, bot, job, offers) -> None:
    text = build_offer_escalation_text(job=job, offers=offers)

    for admin_id in ADMIN_TELEGRAM_USER_IDS:
        await bot.send_message(chat_id=admin_id, text=text)


async def escalate_job_to_manual_review(
    *,
    bot,
    job,
    job_repository,
) -> None:
    offers = await job_repository.list_offers_by_job(job.id)
    await job_repository.update_job_status(
        job_id=job.id,
        status=JobStatus.MANUAL_REVIEW_REQUIRED,
        updated_at=job.updated_at,
    )
    await notify_admins_about_unassigned_job(
        bot=bot,
        job=job,
        offers=offers,
    )
