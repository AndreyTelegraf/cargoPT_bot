import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.handlers.job_contact_phone import router as phone_router
from app.bot.handlers.job_contact_whatsapp import router as whatsapp_router
from app.bot.handlers.job_start import USERNAME_TEXT
from app.bot.job_request_keyboards import phone_skip_keyboard
from app.bot.job_request_keyboards import username_ready_keyboard
from app.bot.job_request_keyboards import whatsapp_keyboard
from app.bot.states.job_request import JobRequestStates
from app.models.job import Job

assert phone_router is not None
assert whatsapp_router is not None
assert username_ready_keyboard() is not None
assert phone_skip_keyboard() is not None
assert whatsapp_keyboard() is not None
assert JobRequestStates.telegram_username_missing is not None
assert JobRequestStates.contact_phone is not None
assert JobRequestStates.contact_whatsapp is not None
assert hasattr(Job, "client_telegram_username")
assert hasattr(Job, "client_phone")
assert hasattr(Job, "client_whatsapp")
assert "Telegram username" in USERNAME_TEXT

print("JOB_CLIENT_CONTACTS_SMOKE_OK")
