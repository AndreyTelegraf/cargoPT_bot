import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.handlers.job_comment import router
from app.repositories.carrier import CarrierRepository

assert router is not None
assert hasattr(CarrierRepository, "get_carrier_by_vehicle_id")

print("JOB_OFFER_SEND_HANDLER_SMOKE_OK")
