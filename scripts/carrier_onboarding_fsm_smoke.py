import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.states.carrier_onboarding import CarrierOnboardingStates

assert CarrierOnboardingStates.assembly_required
assert CarrierOnboardingStates.packing_required
assert CarrierOnboardingStates.operating_regions
assert CarrierOnboardingStates.vehicles

print("CARRIER_ONBOARDING_FSM_SMOKE_OK")
