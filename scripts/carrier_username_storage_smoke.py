import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.models.carrier import CarrierCompany
from app.repositories.carrier import CarrierRepository

source = Path("app/models/carrier.py").read_text(encoding="utf-8")
repo_source = Path("app/repositories/carrier.py").read_text(encoding="utf-8")
start_source = Path("app/bot/handlers/start.py").read_text(encoding="utf-8")

assert hasattr(CarrierCompany, "telegram_username")
assert hasattr(CarrierRepository, "get_carrier_by_username")
assert hasattr(CarrierRepository, "update_carrier_telegram_username")
assert "message.from_user.username" in start_source
assert "update_carrier_telegram_username" in start_source
assert "telegram_username.ilike(cleaned)" in repo_source

print("CARRIER_USERNAME_STORAGE_SMOKE_OK")
