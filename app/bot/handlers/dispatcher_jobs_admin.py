import html

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.handlers.carrier_invite_admin import ADMIN_TELEGRAM_USER_IDS
from app.db.session import async_session_maker
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
    return (
        f"<b>#{job.id}</b> — {_safe(_format_status(job.status))} — @{_safe(client)}\n"
        f"Дата: {_format_dt(job.requested_date)}\n"
        f"Назначена: {_format_dt(job.assigned_at)} | "
        f"Старт: {_format_dt(job.started_at)} | "
        f"Завершена: {_format_dt(job.completed_at)} | "
        f"Отменена: {_format_dt(job.cancelled_at)}"
    )


@router.message(Command("jobs"))
async def dispatcher_jobs(message: Message) -> None:
    if message.from_user.id not in ADMIN_TELEGRAM_USER_IDS:
        await message.answer("Команда доступна только диспетчеру CargoPT.")
        return

    async with async_session_maker() as session:
        repository = JobRepository(session)
        jobs = await repository.list_recent_jobs(limit=20)

    if not jobs:
        await message.answer("Заявок пока нет.")
        return

    text = "<b>Последние заявки CargoPT</b>\n\n" + "\n\n".join(
        _format_job_line(job) for job in jobs
    )

    await message.answer(text, parse_mode="HTML")
