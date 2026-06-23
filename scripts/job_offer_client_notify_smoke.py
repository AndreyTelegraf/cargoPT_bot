import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from types import SimpleNamespace

from app.bot.handlers.job_offer_response import _build_carrier_notification_text
from app.bot.handlers.job_offer_response import _build_client_notification_text
from app.bot.handlers.job_offer_response import router

assert router is not None

job = SimpleNamespace(
    id=42,
    client_telegram_username="client_user",
    client_phone="+351910000000",
    client_whatsapp="+351920000000",
)
carrier = SimpleNamespace(
    company_name="Carrier & Co",
    contact_name="João",
    phone="+351930000000",
    telegram_user_id=123456789,
)

client_text = _build_client_notification_text(job, carrier)
carrier_text = _build_carrier_notification_text(job)

assert "Перевозчик принял вашу заявку #42." in client_text
assert "Компания: Carrier &amp; Co" in client_text
assert "Контактное имя: João" in client_text
assert "Телефон: +351930000000" in client_text
assert "Telegram: 123456789" in client_text

assert "Вы приняли заказ #42." in carrier_text
assert "Telegram: @client_user" in carrier_text
assert "Телефон: +351910000000" in carrier_text
assert "WhatsApp: +351920000000" in carrier_text

print("JOB_OFFER_CLIENT_NOTIFY_SMOKE_OK")
