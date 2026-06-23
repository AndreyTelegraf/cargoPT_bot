import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

source = Path("app/bot/handlers/start.py").read_text(encoding="utf-8")
assert "CommandStart" in source
assert "start_job_request" in source
assert "CargoPT bot is running" not in source

job_start = Path("app/bot/handlers/job_start.py").read_text(encoding="utf-8")
assert "first_question_keyboard" in job_start
assert "Помощь" in Path("app/bot/job_request_keyboards.py").read_text(encoding="utf-8")
assert "Мои объявления" in Path("app/bot/job_request_keyboards.py").read_text(encoding="utf-8")

print("START_ENTRYPOINT_SMOKE_OK")
