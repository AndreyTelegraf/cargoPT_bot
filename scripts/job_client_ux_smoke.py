import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.job_request_keyboards import comment_skip_keyboard
from app.bot.job_request_keyboards import loaders_keyboard
from app.bot.job_request_keyboards import media_skip_keyboard
from app.bot.job_request_keyboards import payload_keyboard
from app.bot.job_request_keyboards import volume_keyboard
from app.bot.job_request_keyboards import yes_no_keyboard

assert yes_no_keyboard() is not None
assert payload_keyboard() is not None
assert volume_keyboard() is not None
assert loaders_keyboard() is not None
assert media_skip_keyboard() is not None
assert comment_skip_keyboard() is not None

from app.bot.handlers import job_comment
from app.bot.handlers import job_crane
from app.bot.handlers import job_item
from app.bot.handlers import job_loaders
from app.bot.handlers import job_media
from app.bot.handlers import job_mobile_lift
from app.bot.handlers import job_payload
from app.bot.handlers import job_start
from app.bot.handlers import job_tail_lift
from app.bot.handlers import job_volume

assert job_start.router is not None
assert job_item.router is not None
assert job_media.router is not None
assert job_payload.router is not None
assert job_volume.router is not None
assert job_loaders.router is not None
assert job_tail_lift.router is not None
assert job_crane.router is not None
assert job_mobile_lift.router is not None
assert job_comment.router is not None

print("JOB_CLIENT_UX_SMOKE_OK")
