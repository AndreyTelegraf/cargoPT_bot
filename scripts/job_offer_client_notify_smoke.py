import os
import sys
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.handlers.job_offer_response import _build_carrier_notification_text
from app.bot.handlers.job_offer_response import _build_client_notification_text
from app.bot.handlers.job_offer_response import router

assert router is not None

job = SimpleNamespace(
    id=42,
    client_telegram_user_id=987654321,
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
carrier_text = _build_carrier_notification_text(job, carrier)

assert "Перевозчик принял вашу заявку #42." in client_text
assert "Я познакомил вас с перевозчиком." in client_text
assert "Компания: Carrier &amp; Co" in client_text
assert "Контактное лицо: João" in client_text
assert "Телефон: +351930000000" in client_text
assert 'Telegram: <a href="tg://user?id=123456789">João</a>' in client_text
assert "Telegram: 123456789" not in client_text

assert "Вы приняли заказ #42." in carrier_text
assert "Я познакомил вас с клиентом." in carrier_text
assert 'Клиент: <a href="tg://user?id=987654321">client_user</a>' in carrier_text
assert "Username: @client_user" in carrier_text
assert "Телефон: +351910000000" in carrier_text
assert "WhatsApp: +351920000000" in carrier_text
assert "Telegram: 987654321" not in carrier_text

print("JOB_OFFER_CLIENT_NOTIFY_SMOKE_OK")
