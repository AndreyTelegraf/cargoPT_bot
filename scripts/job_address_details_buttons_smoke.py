import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.handlers import job_address_details
from app.bot.job_request_keyboards import elevator_keyboard
from app.bot.job_request_keyboards import floor_keyboard
from app.bot.states.job_request import JobRequestStates

assert hasattr(JobRequestStates, "pickup_elevator")
assert hasattr(JobRequestStates, "dropoff_elevator")
assert floor_keyboard() is not None
assert elevator_keyboard() is not None

assert job_address_details._parse_floor("0") == 0
assert job_address_details._parse_floor("24") == 24
assert job_address_details._parse_floor("Подвал") == -1
assert job_address_details._parse_elevator("Да") is True
assert job_address_details._parse_elevator("Нет") is False

for bad in ["25", "-2", "abc"]:
    try:
        job_address_details._parse_floor(bad)
    except ValueError:
        pass
    else:
        raise SystemExit("bad floor accepted: " + bad)

print("JOB_ADDRESS_DETAILS_BUTTONS_SMOKE_OK")
