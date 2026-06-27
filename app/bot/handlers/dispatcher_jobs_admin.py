import html

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

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
