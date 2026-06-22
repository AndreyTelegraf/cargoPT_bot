from aiogram import Router
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.db.session import async_session_maker
from app.repositories.carrier import CarrierRepository
from app.services.carrier_onboarding import CarrierOnboardingService
from app.domain.carrier_profile_step import CarrierProfileStep
from app.bot.states.carrier_onboarding import CarrierOnboardingStates

router = Router()


@router.message(
    CarrierOnboardingStates.operating_regions,
    F.text
)
async def operating_regions(
    message: Message,
    state: FSMContext,
) -> None:

    regions = (message.text or "").strip()

    data = await state.get_data()
    carrier_id = data["carrier_id"]

    async with async_session_maker() as session:
        repository = CarrierRepository(session)
        service = CarrierOnboardingService(repository)

        await service.complete_profile(
            carrier_id=carrier_id,
            assembly_required=data["assembly_required"],
            packing_required=data["packing_required"],
            operating_regions=regions,
        )

        await service.advance_profile_step(
            carrier_id=carrier_id,
            step=CarrierProfileStep.VEHICLES,
        )

        await session.commit()

    await state.update_data(
        operating_regions=regions
    )

    await message.answer(
        "Сколько автомобилей у вашей компании?"
    )
