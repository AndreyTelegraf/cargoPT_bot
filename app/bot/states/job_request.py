from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup


class JobRequestStates(StatesGroup):
    telegram_username_missing = State()
    pickup_address = State()
    pickup_details = State()
    dropoff_address = State()
    dropoff_details = State()
    requested_datetime = State()
    item_description = State()
    media = State()
    estimated_payload_kg = State()
    estimated_volume_m3 = State()
    required_loaders = State()
    needs_tail_lift = State()
    needs_crane = State()
    needs_mobile_lift = State()
    needs_assembly = State()
    needs_packing = State()
    contact_phone = State()
    contact_whatsapp = State()
    comment = State()
