import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.handlers.job_comment import _format_job_details


class Job:
    estimated_payload_kg = 1000
    estimated_volume_m3 = 3.0
    required_loaders = 2
    needs_tail_lift = True
    needs_crane = False
    needs_mobile_lift = False
    comment = "test comment"


class Item:
    description = "диван, коробки, стиральная машина"


payload = _format_job_details(Job(), [Item()])

assert "Груз: диван, коробки, стиральная машина" in payload
assert "Вес: 1000 кг" in payload
assert "Объём: 3.0 м³" in payload
assert "Грузчики: 2" in payload
assert "Гидроборт: да" in payload
assert "Кран: нет" in payload
assert "Мобильный лифт / подъём через окно: нет" in payload
assert "Комментарий: test comment" in payload

print("JOB_OFFER_PAYLOAD_SMOKE_OK")
