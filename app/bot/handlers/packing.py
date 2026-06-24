from aiogram import Router
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.handlers.invite import carrier_yes_no_keyboard
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

        await service.complete_profile(
            carrier_id=carrier_id,
            assembly_required=data["assembly_required"],
            packing_required=packing_required,
            operating_regions=data["operating_regions"],
        )

        await session.commit()

    await state.update_data(
        packing_required=packing_required,
    )

    await state.set_state(CarrierOnboardingStates.has_tail_lift)

    await message.answer(
        "Есть ли гидроборт?",
        reply_markup=carrier_yes_no_keyboard(),
    )
