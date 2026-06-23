import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.assignment_confirmation_keyboard import build_assignment_confirmation_keyboard
from app.bot.handlers.job_assignment_confirmation import _parse_assignment_callback
from app.bot.handlers.job_assignment_confirmation import handle_assignment_confirmation
from app.bot.handlers.job_assignment_confirmation import router

assert router is not None
assert handle_assignment_confirmation is not None

keyboard = build_assignment_confirmation_keyboard(42)
buttons = keyboard.inline_keyboard[0]

assert buttons[0].text == "Сделка подтверждена"
assert buttons[0].callback_data == "assignment:confirm:42"
assert buttons[1].text == "Не договорились"
assert buttons[1].callback_data == "assignment:fail:42"

assert _parse_assignment_callback("assignment:confirm:42") == ("confirm", 42)
assert _parse_assignment_callback("assignment:fail:42") == ("fail", 42)

handler_source = Path("app/bot/handlers/job_assignment_confirmation.py").read_text(encoding="utf-8")
assert "confirm_assignment" in handler_source
assert "reopen_assignment_search" in handler_source
assert "ASSIGNED_PENDING_CONFIRMATION" in handler_source
assert "edit_reply_markup(reply_markup=None)" in handler_source

offer_response_source = Path("app/bot/handlers/job_offer_response.py").read_text(encoding="utf-8")
assert "build_assignment_confirmation_keyboard(job.id)" in offer_response_source
assert "reply_markup=confirmation_keyboard" in offer_response_source

router_source = Path("app/bot/routers.py").read_text(encoding="utf-8")
assert "job_assignment_confirmation_router" in router_source

print("JOB_ASSIGNMENT_CONFIRMATION_SMOKE_OK")
