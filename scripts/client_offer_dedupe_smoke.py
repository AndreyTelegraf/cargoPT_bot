import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

source = Path("app/bot/handlers/job_offer_response.py").read_text(encoding="utf-8")

assert "accepted_offer_count = sum(" in source
assert "if job is not None and accepted_offer_count == 1:" in source
assert "send_client_offer_selection_message(" in source

print("CLIENT_OFFER_DEDUPE_SMOKE_OK")
