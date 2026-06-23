import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.handlers.job_offer_response import _finalize_offer_message
from app.bot.handlers.job_offer_response import router
from app.bot.offer_keyboard import build_offer_keyboard

assert router is not None
assert _finalize_offer_message is not None

keyboard = build_offer_keyboard(123)
assert keyboard.inline_keyboard[0][0].callback_data == "offer:accept:123"
assert keyboard.inline_keyboard[0][1].callback_data == "offer:decline:123"

source = Path("app/bot/handlers/job_offer_response.py").read_text(encoding="utf-8")
assert "edit_text(text, parse_mode=\"HTML\", reply_markup=reply_markup)" in source
assert "edit_caption(caption=text, parse_mode=\"HTML\", reply_markup=reply_markup)" in source
assert "edit_reply_markup(reply_markup=reply_markup)" in source
assert "build_assignment_confirmation_keyboard(job.id)" in source

print("JOB_OFFER_RESPONSE_HANDLER_SMOKE_OK")
