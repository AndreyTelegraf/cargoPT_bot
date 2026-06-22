from aiogram import Router
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.carrier_onboarding import CarrierOnboardingStates

router = Router()


@router.message(
    CarrierOnboardingStates.assembly_required,
    F.text.in_(["Да", "Нет"])
)
async def assembly_required(
    message: Message,
    state: FSMContext,
) -> None:

    assembly_required = message.text == "Да"

    await state.update_data(
        assembly_required=assembly_required
    )

    await state.set_state(
        CarrierOnboardingStates.packing_required
    )

    await message.answer(
        "Предоставляете ли вы услуги упаковки груза? (Да/Нет)"
    )
