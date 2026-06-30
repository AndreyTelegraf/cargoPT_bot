import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.handlers.job_offer_response import build_client_assignment_confirmation_text
from app.bot.handlers.job_offer_response import send_assignment_confirmation_requests

text = build_client_assignment_confirmation_text(456)
assert "Предложение по заявке №456 выбрано." in text
assert "Подтвердите сделку" in text

source = Path("app/bot/handlers/job_offer_response.py").read_text(encoding="utf-8")
helper_block = source[
    source.index("async def send_assignment_confirmation_requests"):
    source.index("@router.callback_query(F.data.startswith(\"offer:\"))")
]
client_handler = source[source.index("async def handle_client_offer_selection"):]

assert "client_telegram_user_id" not in helper_block
assert "client_telegram_user_id=" not in client_handler
assert "callback.message.edit_text(" in client_handler
assert "reply_markup=build_assignment_confirmation_keyboard(job_id)" in client_handler
assert "send_assignment_confirmation_requests(" in client_handler

print("CLIENT_OFFER_REUSE_ASSIGNMENT_MESSAGE_SMOKE_OK")
