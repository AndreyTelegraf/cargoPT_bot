import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.domain.job_status import JobStatus

assert JobStatus.NO_CARRIERS_FOUND == "no_carriers_found"
assert JobStatus.OFFERS_EXHAUSTED == "offers_exhausted"
assert JobStatus.EXPIRED_WITHOUT_RESPONSE == "expired_without_response"

offer_distribution = Path("app/services/offer_distribution.py").read_text()
offer_expiry = Path("app/services/offer_expiry.py").read_text()
offer_response = Path("app/bot/handlers/job_offer_response.py").read_text()

assert "JobStatus.NO_CARRIERS_FOUND" in offer_distribution
assert "JobStatus.EXPIRED_WITHOUT_RESPONSE" in offer_expiry
assert "JobStatus.OFFERS_EXHAUSTED" in offer_expiry
assert "JobStatus.OFFERS_EXHAUSTED" in offer_response

print("JOB_UNMATCHED_STATUS_SPLIT_SMOKE_OK")
