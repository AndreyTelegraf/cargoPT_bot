import os
import sys
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.handlers.job_comment import _build_offer_text

job = SimpleNamespace(
    id=9,
    requested_date=None,
    estimated_payload_kg=1000,
    estimated_volume_m3=3.0,
    required_loaders=2,
    needs_tail_lift=True,
    needs_crane=False,
    needs_mobile_lift=False,
    comment="test comment",
    client_telegram_username="client_user",
    client_phone="+351910000000",
    client_whatsapp="+351910000000",
)

item = SimpleNamespace(description="диван, коробки, стиральная машина")
pickup = SimpleNamespace(raw_text="Lisboa", map_url="https://maps.app.goo.gl/pickup")
dropoff = SimpleNamespace(raw_text="Cascais", map_url="https://maps.app.goo.gl/dropoff")

payload = _build_offer_text(job, [item], pickup, dropoff)

assert "\\n" not in payload
assert "Новая заявка #9" in payload
assert "Груз\nдиван, коробки, стиральная машина" in payload
assert "Вес: 1000 кг" in payload
assert "Объём: 3.0 м³" in payload
assert "Грузчики: 2" in payload
assert "Гидроборт: да" in payload
assert "Кран: нет" in payload
assert "Подъём через окно: нет" in payload
assert "Комментарий\ntest comment" in payload
assert "Telegram: @client_user" in payload

print("JOB_OFFER_PAYLOAD_SMOKE_OK")
