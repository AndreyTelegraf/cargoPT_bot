import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.handlers.job_offer_response import build_client_offer_selection_text
from app.bot.handlers.job_offer_response import handle_client_offer_selection
from app.bot.handlers.job_offer_response import send_client_offer_selection_message
from app.bot.offer_keyboard import build_client_offer_selection_keyboard
from app.bot.offer_keyboard import parse_client_offer_selection_callback


class View:
    offer_id = 123
    job_id = 456
    company_name = "Carrier <One>"
    vehicle_type = "large_van"
    payload_kg = 1200
    volume_m3 = 14.0
    max_loaders = 2
    price_cents = 12345
    carrier_note = "Careful <move>"
    included_services = "Loading and unloading"
    possible_surcharges = "Tolls if applicable"
    service_window = "12 Sep, 14:00-16:00"
    estimate_status = "final"


job_id, offer_id = parse_client_offer_selection_callback("client_offer:select:456:123")
assert job_id == 456
assert offer_id == 123

keyboard = build_client_offer_selection_keyboard([View()])
assert keyboard.inline_keyboard[0][0].callback_data == "client_offer:select:456:123"
assert keyboard.inline_keyboard[0][0].text == "Выбрать предложение 1"

assert build_client_offer_selection_keyboard(
    [View()], "pt"
).inline_keyboard[0][0].text == "Escolher proposta 1"

text = build_client_offer_selection_text(456, [View()])
assert "Перевозчики откликнулись на заявку №456" in text
assert "Carrier &lt;One&gt;" in text
assert "Careful &lt;move&gt;" in text
assert "123.45 €" in text
assert "Loading and unloading" in text
assert "Tolls if applicable" in text
assert "12 Sep, 14:00-16:00" in text
assert "окончательная" in text

english_text = build_client_offer_selection_text(456, [View()], "en")
assert "Carriers responded to request #456" in english_text
assert "Included services: Loading and unloading" in english_text
assert "Possible extras: Tolls if applicable" in english_text
assert "Service date / time window: 12 Sep, 14:00-16:00" in english_text
assert "Price type: final" in english_text

portuguese_text = build_client_offer_selection_text(456, [View()], "pt")
assert "Os transportadores responderam ao pedido #456" in portuguese_text
assert "Serviços incluídos: Loading and unloading" in portuguese_text
assert "Possíveis extras: Tolls if applicable" in portuguese_text
assert "Tipo de preço: definitivo" in portuguese_text

assert handle_client_offer_selection is not None
assert send_client_offer_selection_message is not None

source = Path("app/bot/handlers/job_offer_response.py").read_text(encoding="utf-8")
assert "select_accepted_offer_for_client" in source
assert "build_client_reopen_assignment_keyboard" in source
assert "ClientOfferPresentationService" in source
assert "client_offer:select" in Path("app/bot/offer_keyboard.py").read_text(encoding="utf-8")

print("CLIENT_OFFER_SELECTION_UI_SMOKE_OK")
