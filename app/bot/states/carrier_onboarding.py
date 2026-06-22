from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup


class CarrierOnboardingStates(StatesGroup):
    assembly_required = State()
    packing_required = State()
    operating_regions = State()
    vehicles = State()
