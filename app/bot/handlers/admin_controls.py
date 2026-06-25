from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.handlers.carrier_invite_admin import ADMIN_TELEGRAM_USER_IDS
from app.db.session import async_session_maker
from app.repositories.job import JobRepository

router = Router()


def _is_admin(message: Message) -> bool:
    return message.from_user is not None and message.from_user.id in ADMIN_TELEGRAM_USER_IDS


@router.message(Command("ban"))
async def ban_client(message: Message) -> None:
    if not _is_admin(message):
        await message.answer("Команда доступна только администратору CargoPT.")
        return

    parts = (message.text or "").split(maxsplit=2)

    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Формат: /ban <telegram_user_id> [причина]")
        return

    telegram_user_id = int(parts[1])
    reason = parts[2] if len(parts) > 2 else None

    async with async_session_maker() as session:
        repo = JobRepository(session)

        await repo.ban_client(
            telegram_user_id=telegram_user_id,
            username=None,
            reason=reason,
            banned_by_admin_id=message.from_user.id,
        )

        await session.commit()

    await message.answer(f"Клиент {telegram_user_id} заблокирован.")


@router.message(Command("unban"))
async def unban_client(message: Message) -> None:
    if not _is_admin(message):
        await message.answer("Команда доступна только администратору CargoPT.")
        return

    parts = (message.text or "").split(maxsplit=1)

    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Формат: /unban <telegram_user_id>")
        return

    telegram_user_id = int(parts[1])

    async with async_session_maker() as session:
        repo = JobRepository(session)

        ban = await repo.unban_client(
            telegram_user_id=telegram_user_id,
            unbanned_by_admin_id=message.from_user.id,
        )

        await session.commit()

    if ban is None:
        await message.answer("Активная блокировка не найдена.")
    else:
        await message.answer(f"Клиент {telegram_user_id} разблокирован.")
