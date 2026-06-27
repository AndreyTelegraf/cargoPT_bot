from pathlib import Path

pickup = Path("app/bot/handlers/job_pickup.py").read_text()
dropoff = Path("app/bot/handlers/job_dropoff.py").read_text()

assert 'not raw_text or raw_text.startswith("/")' in pickup
assert 'not raw_text or raw_text.startswith("/")' in dropoff
assert 'service.add_address' in pickup
assert 'service.add_address' in dropoff

print("JOB_ADDRESS_COMMAND_GUARD_SMOKE_OK")
