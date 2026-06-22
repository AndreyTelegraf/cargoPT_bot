from aiogram import Router
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.carrier_onboarding import CarrierOnboardingStates

router = Router()

@router.message(
    CarrierOnboardingStates.packing_required,
    F.text.in_(["Да","Нет"])
)
async def packing_required(
    message: Message,
    state: FSMContext,
) -> None:

    await state.update_data(
        packing_required=(message.text == "Да")
    )

    await message.answer(
        "В каких регионах Португалии вы работаете?"
    )
