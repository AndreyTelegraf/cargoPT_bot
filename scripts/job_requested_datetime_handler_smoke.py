import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.handlers.job_requested_datetime import _parse_requested_datetime
from app.bot.handlers.job_requested_datetime import router

assert router is not None
assert _parse_requested_datetime("Завтра") is not None
assert _parse_requested_datetime("24.06 10:00") is not None
assert _parse_requested_datetime("24.06.2026 15:30") is not None

print("JOB_REQUESTED_DATETIME_HANDLER_SMOKE_OK")
