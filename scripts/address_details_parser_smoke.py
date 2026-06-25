import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.handlers.job_address_details import _parse_floor_elevator

cases = {
    "5, да": (5, True),
    "5 да": (5, True),
    "5 этаж, лифт есть": (5, True),
    "на 5 этаже есть лифт": (5, True),
    "2 без лифта": (2, False),
    "этаж 3, лифта нет": (3, False),
    "0, нет": (0, False),
    "-1, да": (-1, True),
    "r/c, com elevador": (0, True),
    "rés-do-chão sem elevador": (0, False),
    "floor 4 with elevator": (4, True),
    "3rd floor no elevator": (3, False),
    "пятый этаж, без лифта": (5, False),
    "подвал, лифт есть": (-1, True),
    "7": (7, None),
}

for raw, expected in cases.items():
    result = _parse_floor_elevator(raw)
    if result != expected:
        raise SystemExit(f"{raw!r}: expected {expected}, got {result}")

invalid = ["", "лифт есть", "без лифта", "этаж неизвестен"]
for raw in invalid:
    try:
        _parse_floor_elevator(raw)
    except ValueError:
        continue
    raise SystemExit(f"{raw!r}: expected ValueError")

print("ADDRESS_DETAILS_PARSER_SMOKE_OK")
