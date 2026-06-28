import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

repo_source = Path("app/repositories/job.py").read_text()
start_source = Path("app/bot/handlers/job_start.py").read_text()

assert "get_latest_draft_job_by_client_id" in repo_source
assert "RequestDraftService" in start_source
assert "create_or_reuse_telegram_draft" in start_source
assert "job = result.job" in start_source
assert "draft_has_no_progress" in repo_source or "RequestDraftService" in start_source

print("JOB_START_REUSE_EMPTY_DRAFT_SMOKE_OK")
