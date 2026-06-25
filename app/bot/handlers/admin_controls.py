from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.auth import admin_only
from app.db import async_session_maker
from app.repositories.job import JobRepository

router = Router()


@router.message(Command("ban"))
@admin_only
async def ban_client(message: Message) -> None:
    parts = message.text.split(maxsplit=2)

    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Usage: /ban <telegram_user_id> [reason]")
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

    await message.answer(f"Client {telegram_user_id} banned.")


@router.message(Command("unban"))
@admin_only
async def unban_client(message: Message) -> None:
    parts = message.text.split(maxsplit=1)

    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Usage: /unban <telegram_user_id>")
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
        await message.answer("Active ban not found.")
    else:
        await message.answer(f"Client {telegram_user_id} unbanned.")
