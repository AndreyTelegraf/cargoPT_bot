import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.handlers.job_media import router
from app.bot.states.job_request import JobRequestStates
from app.models.job import JobMedia
from app.repositories.job import JobRepository

assert router is not None
assert JobRequestStates.media
assert JobMedia.__tablename__ == "job_media"
assert hasattr(JobRepository, "add_media")
assert hasattr(JobRepository, "list_media_by_job")

print("JOB_MEDIA_HANDLER_SMOKE_OK")
