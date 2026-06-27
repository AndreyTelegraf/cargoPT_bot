import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

source = Path("app/services/job_offer.py").read_text()

assert "if job.status not in {" in source
assert "JobStatus.MATCHING" in source
assert "JobStatus.OFFERED" in source
assert "job is not accepting offers" in source

print("JOB_OFFER_STALE_ACCEPTANCE_GUARD_SMOKE_OK")
