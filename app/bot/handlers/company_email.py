from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.carrier_onboarding import CarrierOnboardingStates

from app.db.session import async_session_maker
from app.repositories.carrier import CarrierRepository
from app.services.carrier_vehicle import CarrierVehicleService

router = Router()


@router.message(CarrierOnboardingStates.company_email)
async def company_email(
    message: Message,
    state: FSMContext,
) -> None:

    email = message.text.strip()

    if "@" not in email or "." not in email:
        return

    await state.update_data(
        company_email=email
    )

    data = await state.get_data()
    carrier_id = data["carrier_id"]

    async with async_session_maker() as session:
        repository = CarrierRepository(session)
        service = CarrierVehicleService(repository)

        await service.create_vehicle(
            carrier_id=carrier_id,
            vehicle_type=data["vehicle_type"],
            payload_kg=data["payload_kg"],
            volume_m3=data["volume_m3"],
            has_tail_lift=data["has_tail_lift"],
            has_crane=data["has_crane"],
            has_mobile_lift=data["has_mobile_lift"],
            mobile_lift_max_floor=data.get("mobile_lift_max_floor"),
            mobile_lift_max_weight_kg=data.get("mobile_lift_max_weight_kg"),
            crane_max_weight_kg=data.get("crane_max_weight_kg"),
            crane_reach_meters=data.get("crane_max_reach_m"),
        )

        await session.commit()

    await state.clear()

    await message.answer(
        "Профиль перевозчика сохранён. Спасибо."
    )
