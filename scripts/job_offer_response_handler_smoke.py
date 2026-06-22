import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.handlers.job_offer_response import router
from app.bot.offer_keyboard import build_offer_keyboard

assert router is not None
keyboard = build_offer_keyboard(123)
assert keyboard.inline_keyboard[0][0].callback_data == "offer:accept:123"
assert keyboard.inline_keyboard[0][1].callback_data == "offer:decline:123"

print("JOB_OFFER_RESPONSE_HANDLER_SMOKE_OK")
