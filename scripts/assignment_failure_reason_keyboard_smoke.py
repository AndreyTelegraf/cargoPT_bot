import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.assignment_confirmation_keyboard import build_assignment_failure_reason_keyboard
from app.domain.job_decline_reason import DECLINE_REASON_LABELS
from app.domain.job_decline_reason import DECLINE_REASONS
from app.domain.job_decline_reason import UNSPECIFIED_DECLINE_REASON
from app.domain.job_decline_reason import get_decline_reason_label
from app.domain.job_decline_reason import is_valid_decline_reason

assert len(DECLINE_REASONS) == 8
assert DECLINE_REASON_LABELS["price_not_agreed"] == "Не договорились по цене"
assert is_valid_decline_reason("client_unreachable") is True
assert is_valid_decline_reason(UNSPECIFIED_DECLINE_REASON) is True
assert is_valid_decline_reason("bad_reason") is False
assert get_decline_reason_label(None) == "Не указано"

keyboard = build_assignment_failure_reason_keyboard(123)
buttons = [
    button
    for row in keyboard.inline_keyboard
    for button in row
]
callback_data = [button.callback_data for button in buttons]

assert len(buttons) == 8
assert "assignment:fail_reason:123:price_not_agreed" in callback_data
assert "assignment:fail_reason:123:other" in callback_data

print("ASSIGNMENT_FAILURE_REASON_KEYBOARD_SMOKE_OK")
