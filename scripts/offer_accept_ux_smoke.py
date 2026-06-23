import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

source = Path("app/bot/handlers/job_offer_response.py").read_text(encoding="utf-8")
assert '"Перевозчик принял вашу заявку.\\n"' not in source
assert '"Перевозчик принял вашу заявку.\\n"' not in source
assert "Заявка #{job.id} закреплена за вами" in source
assert "edit_reply_markup" in source

print("OFFER_ACCEPT_UX_SMOKE_OK")
