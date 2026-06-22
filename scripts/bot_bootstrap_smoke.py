import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

from app.bot.dispatcher import build_dispatcher

bot, dp = build_dispatcher()

assert bot is not None
assert dp is not None

print("BOT_BOOTSTRAP_SMOKE_OK")
