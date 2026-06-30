import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

source = Path("app/bot/handlers/job_offer_response.py").read_text(encoding="utf-8")

assert "Предложение выбрано. Заявка №{job_id} отправлена на подтверждение сделки." in source
assert "reply_markup=None" in source[source.index("async def handle_client_offer_selection"):]

print("CLIENT_OFFER_MESSAGE_CLEANUP_SMOKE_OK")
