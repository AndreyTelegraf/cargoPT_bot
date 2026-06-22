from aiogram import Router
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.carrier_onboarding import CarrierOnboardingStates
from app.db.session import async_session_maker
from app.repositories.carrier import CarrierRepository
from app.services.carrier_onboarding import CarrierOnboardingService
from app.domain.carrier_profile_step import CarrierProfileStep

router = Router()

@router.message(
    CarrierOnboardingStates.packing_required,
    F.text.in_(["Да","Нет"])
)
async def packing_required(
    message: Message,
    state: FSMContext,
) -> None:

    packing_required = (message.text == "Да")

    data = await state.get_data()
    carrier_id = data["carrier_id"]

    async with async_session_maker() as session:
        repository = CarrierRepository(session)
        service = CarrierOnboardingService(repository)

        await service.save_packing_required(
            carrier_id=carrier_id,
            value=packing_required,
        )

        await service.advance_profile_step(
            carrier_id=carrier_id,
            step=CarrierProfileStep.OPERATING_REGIONS,
        )

        await session.commit()

    await state.update_data(
        packing_required=packing_required
    )

    await message.answer(
        "В каких регионах Португалии вы работаете?"
    )
