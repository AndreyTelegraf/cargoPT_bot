from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.handlers.invite import carrier_yes_no_keyboard
from app.db.session import async_session_maker
from app.domain.carrier_profile_step import CarrierProfileStep
from app.repositories.carrier import CarrierRepository
from app.services.carrier_onboarding import CarrierOnboardingService
from app.bot.states.carrier_onboarding import CarrierOnboardingStates

router = Router()


@router.message(CarrierOnboardingStates.volume_m3)
async def volume_m3(
    message: Message,
    state: FSMContext,
) -> None:

    try:
        volume = float(
            message.text.replace(",", ".")
        )
    except Exception:
        return

    if volume <= 0:
        return

    await state.update_data(
        volume_m3=volume
    )

    data = await state.get_data()

    if "assembly_required" in data and "packing_required" in data:
        await state.set_state(CarrierOnboardingStates.has_tail_lift)
        await message.answer(
            "Есть ли гидроборт?",
            reply_markup=carrier_yes_no_keyboard(),
        )
        return

    carrier_id = data["carrier_id"]

    async with async_session_maker() as session:
        repository = CarrierRepository(session)
        service = CarrierOnboardingService(repository)
        await service.advance_profile_step(
            carrier_id=carrier_id,
            step=CarrierProfileStep.ASSEMBLY_REQUIRED,
        )
        await session.commit()

    await state.set_state(CarrierOnboardingStates.assembly_required)

    await message.answer(
        "Предоставляете ли вы услуги сборки и разборки мебели?",
        reply_markup=carrier_yes_no_keyboard(),
    )
