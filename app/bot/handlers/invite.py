from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.db.session import async_session_maker
from app.repositories.carrier import CarrierRepository
from app.services.carrier_onboarding import CarrierOnboardingService

router = Router()


@router.message(CommandStart(deep_link=True))
async def invite_start(message: Message) -> None:
    payload = (message.text or "").split(maxsplit=1)

    if len(payload) != 2:
        await message.answer(
            "У вас нет приглашения. Обратитесь к администратору CargoPT."
        )
        return

    token = payload[1].strip()

    async with async_session_maker() as session:
        repository = CarrierRepository(session)
        service = CarrierOnboardingService(repository)

        try:
            invite = await service.claim_invite_token(
                token=token,
                telegram_user_id=message.from_user.id,
            )
            await session.commit()

        except Exception:
            await session.rollback()
            await message.answer(
                "Приглашение недействительно или уже использовано."
            )
            return

    await message.answer(
        f"Компания #{invite.carrier_id} успешно привязана."
    )
