from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup


class JobRequestStates(StatesGroup):
    pickup_address = State()
    dropoff_address = State()
    item_description = State()
    estimated_payload_kg = State()
    estimated_volume_m3 = State()
    required_loaders = State()
    needs_tail_lift = State()
    needs_crane = State()
    needs_mobile_lift = State()
    comment = State()
