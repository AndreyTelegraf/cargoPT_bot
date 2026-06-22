import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.handlers.job_comment import job_comment
from app.bot.handlers.job_comment import router

assert router is not None
assert job_comment is not None

source = Path("app/bot/handlers/job_comment.py").read_text(encoding="utf-8")
assert "list_media_by_job" in source
assert "send_photo" in source
assert "send_video" in source
assert "Медиа к заявке" in source

print("JOB_OFFER_SEND_MEDIA_HANDLER_SMOKE_OK")
