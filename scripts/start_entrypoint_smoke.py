import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.handlers.start import start_handler
from app.bot.handlers.job_start import start_job_request_entry
from app.bot.job_request_keyboards import client_entry_keyboard

assert start_handler is not None
assert start_job_request_entry is not None
keyboard = client_entry_keyboard()
texts = [button.text for row in keyboard.keyboard for button in row]
assert "Помощь" in texts
assert "Мои объявления" in texts

print("START_ENTRYPOINT_SMOKE_OK")
