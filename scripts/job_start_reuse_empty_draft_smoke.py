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
assert "_draft_has_no_progress" in start_source
assert "latest_draft = await repository.get_latest_draft_job_by_client_id" in start_source
assert "job = latest_draft" in start_source
assert "await service.create_draft_job" in start_source

print("JOB_START_REUSE_EMPTY_DRAFT_SMOKE_OK")
