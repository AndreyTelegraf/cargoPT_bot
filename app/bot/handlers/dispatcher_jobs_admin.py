import html
from datetime import UTC
from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import text

from app.bot.handlers.carrier_invite_admin import ADMIN_TELEGRAM_USER_IDS
from app.db.session import async_session_maker
from app.domain.job_decline_reason import get_decline_reason_label
from app.repositories.job import JobRepository

router = Router()


def _safe(value) -> str:
    return html.escape(str(value), quote=False)


def _format_dt(value) -> str:
    if value is None:
        return "—"
    return _safe(value.strftime("%d.%m.%Y %H:%M"))


STATUS_LABELS = {
    "draft": "черновик",
    "ready_for_matching": "готова к поиску",
    "matching": "поиск перевозчика",
    "offered": "отправлена перевозчикам",
    "unmatched": "перевозчик не найден",
    "no_carriers_found": "нет подходящих перевозчиков",
    "offers_exhausted": "все перевозчики отказались",
    "expired_without_response": "нет ответов от перевозчиков",
    "manual_review_required": "требует ручного контроля",
    "assigned_pending_confirmation": "ожидает подтверждения сделки",
    "assigned": "перевозчик назначен",
    "in_progress": "в работе",
    "completed": "завершена",
    "cancelled": "отменена",
}


def _format_status(value: str) -> str:
    return STATUS_LABELS.get(value, value)


def _format_job_line(job) -> str:
    client = job.client_telegram_username or str(job.client_telegram_user_id)
    line = (
        f"<b>#{job.id}</b> — {_safe(_format_status(job.status))} — @{_safe(client)}\n"
        f"Дата: {_format_dt(job.requested_date)}\n"
        f"Назначена: {_format_dt(job.assigned_at)} | "
        f"Старт: {_format_dt(job.started_at)} | "
        f"Завершена: {_format_dt(job.completed_at)} | "
        f"Отменена: {_format_dt(job.cancelled_at)}"
    )

    offers_count = getattr(job, "offers_count", None)
    if offers_count is not None:
        line += f"\nОфферов: {_safe(offers_count)}"

    attention_reason = getattr(job, "attention_reason", None)
    if attention_reason:
        line += f"\nПричина: {_safe(get_decline_reason_label(attention_reason))}"

    return line


async def _send_jobs_list(
    *,
    message: Message,
    title: str,
    empty_text: str,
    jobs,
) -> None:
    if not jobs:
        await message.answer(empty_text)
        return

    text = title + "\n\n" + "\n\n".join(
        _format_job_line(job) for job in jobs
    )

    await message.answer(text, parse_mode="HTML")

def _format_status_counts(rows) -> str:
    if not rows:
        return "—"
    return "\n".join(
        f"{_safe(_format_status(row['status']))}: {_safe(row['count'])}"
        for row in rows
    )


def _format_offer_counts(rows) -> str:
    if not rows:
        return "—"
    return "\n".join(
        f"{_safe(row['status'])}: {_safe(row['count'])}"
        for row in rows
    )


def _format_report_job_rows(rows) -> str:
    if not rows:
        return "—"

    lines = []
    for row in rows:
        client = row["client_telegram_username"] or str(row["client_telegram_user_id"])
        line = (
            f"<b>#{_safe(row['id'])}</b> — {_safe(_format_status(row['status']))} — @{_safe(client)}\n"
            f"Офферов: {_safe(row['offers'])} | "
            f"accepted: {_safe(row['accepted'])} | "
            f"declined: {_safe(row['declined'])} | "
            f"expired: {_safe(row['expired'])} | "
            f"pending: {_safe(row['pending'])}"
        )
        if row["latest_reason"]:
            line += f"\nПричина: {_safe(get_decline_reason_label(row['latest_reason']))}"
        lines.append(line)

    return "\n\n".join(lines)


@router.message(Command("jobs"))
async def dispatcher_jobs(message: Message) -> None:
    if message.from_user.id not in ADMIN_TELEGRAM_USER_IDS:
        await message.answer("Команда доступна только диспетчеру CargoPT.")
        return

    async with async_session_maker() as session:
        repository = JobRepository(session)
        jobs = await repository.list_recent_jobs(limit=20)

    await _send_jobs_list(
        message=message,
        title="<b>Последние заявки CargoPT</b>",
        empty_text="Заявок пока нет.",
        jobs=jobs,
    )


@router.message(Command("jobs_attention"))
async def dispatcher_jobs_attention(message: Message) -> None:
    if message.from_user.id not in ADMIN_TELEGRAM_USER_IDS:
        await message.answer("Команда доступна только диспетчеру CargoPT.")
        return

    async with async_session_maker() as session:
        repository = JobRepository(session)
        jobs = await repository.list_attention_jobs(limit=20)

    await _send_jobs_list(
        message=message,
        title="<b>Заявки CargoPT, требующие внимания</b>",
        empty_text="Заявок, требующих внимания, нет.",
        jobs=jobs,
    )



@router.message(Command("jobs_report"))
async def dispatcher_jobs_report(message: Message) -> None:
    if message.from_user.id not in ADMIN_TELEGRAM_USER_IDS:
        await message.answer("Команда доступна только диспетчеру CargoPT.")
        return

    since = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    since_text = since.strftime("%Y-%m-%d %H:%M:%S")

    async with async_session_maker() as session:
        job_rows = (
            await session.execute(
                text("""
                    SELECT status, COUNT(*) AS count
                    FROM job
                    WHERE created_at >= :since
                    GROUP BY status
                    ORDER BY count DESC, status
                """),
                {"since": since_text},
            )
        ).mappings().all()

        offer_rows = (
            await session.execute(
                text("""
                    SELECT o.status, COUNT(*) AS count
                    FROM job_offer o
                    JOIN job j ON j.id = o.job_id
                    WHERE j.created_at >= :since
                    GROUP BY o.status
                    ORDER BY count DESC, o.status
                """),
                {"since": since_text},
            )
        ).mappings().all()

        job_detail_rows = (
            await session.execute(
                text("""
                    SELECT
                        j.id,
                        j.status,
                        j.client_telegram_username,
                        j.client_telegram_user_id,
                        COUNT(o.id) AS offers,
                        COALESCE(SUM(CASE WHEN o.status = 'accepted' THEN 1 ELSE 0 END), 0) AS accepted,
                        COALESCE(SUM(CASE WHEN o.status = 'declined' THEN 1 ELSE 0 END), 0) AS declined,
                        COALESCE(SUM(CASE WHEN o.status = 'expired' THEN 1 ELSE 0 END), 0) AS expired,
                        COALESCE(SUM(CASE WHEN o.status = 'pending' THEN 1 ELSE 0 END), 0) AS pending,
                        MAX(o.decline_reason) AS latest_reason
                    FROM job j
                    LEFT JOIN job_offer o ON o.job_id = j.id
                    WHERE j.created_at >= :since
                    GROUP BY j.id
                    ORDER BY j.id
                """),
                {"since": since_text},
            )
        ).mappings().all()

    report = (
        "<b>CargoPT jobs report</b>\n"
        f"Срез: с {_safe(since_text)} UTC\n\n"
        "<b>Заявки</b>\n"
        f"{_format_status_counts(job_rows)}\n\n"
        "<b>Офферы</b>\n"
        f"{_format_offer_counts(offer_rows)}\n\n"
        "<b>По заявкам</b>\n"
        f"{_format_report_job_rows(job_detail_rows)}"
    )

    await message.answer(report, parse_mode="HTML")
