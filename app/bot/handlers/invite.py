from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.db.session import async_session_maker
from app.repositories.carrier import CarrierRepository
from app.services.carrier_onboarding import CarrierOnboardingService
from app.domain.carrier_profile_step import CarrierProfileStep
from app.bot.states.carrier_onboarding import CarrierOnboardingStates

router = Router()


@router.message(CommandStart(deep_link=True))
async def invite_start(message: Message, state: FSMContext) -> None:
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

            carrier = await repository.get_carrier_by_id(invite.carrier_id)

            if carrier is None:
                raise ValueError("carrier not found")

            await service.advance_profile_step(
                carrier_id=invite.carrier_id,
                step=CarrierProfileStep.ASSEMBLY_REQUIRED,
            )

            await session.commit()

        except Exception:
            await session.rollback()
            await message.answer(
                "Приглашение недействительно или уже использовано."
            )
            return

    await state.update_data(
        carrier_id=invite.carrier_id,
        company_name=carrier.company_name,
        contact_name=carrier.contact_name,
    )

    await state.set_state(
        CarrierOnboardingStates.assembly_required
    )

    await message.answer(
        f"Компания:\n{carrier.company_name}\n\n"
        "Продолжим заполнение анкеты.\n\n"
        "Нужна ли вашей компании сборка/разборка мебели? (Да/Нет)"
    )
