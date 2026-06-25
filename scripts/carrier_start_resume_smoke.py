
from pathlib import Path

source = Path("app/bot/handlers/start.py").read_text()

assert "CarrierOnboardingStates.operating_regions" in source
assert "regions_keyboard()" in source
assert "carrier.status == CarrierStatus.INVITED" in source
assert "Вы уже начали анкету перевозчика CargoPT" in source
assert "await start_job_request(message, state)" in source

print("CARRIER_START_RESUME_SMOKE_OK")
