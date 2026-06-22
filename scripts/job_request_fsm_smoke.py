import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.states.job_request import JobRequestStates

assert JobRequestStates.pickup_address
assert JobRequestStates.dropoff_address
assert JobRequestStates.item_description
assert JobRequestStates.estimated_payload_kg
assert JobRequestStates.estimated_volume_m3
assert JobRequestStates.required_loaders
assert JobRequestStates.needs_tail_lift
assert JobRequestStates.needs_crane
assert JobRequestStates.needs_mobile_lift
assert JobRequestStates.comment

print("JOB_REQUEST_FSM_SMOKE_OK")
