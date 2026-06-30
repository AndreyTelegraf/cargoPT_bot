from pathlib import Path

source = Path("app/bot/handlers/carrier_moderation_submit.py").read_text(encoding="utf-8")

assert "redispatch_open_jobs_to_new_carrier" in source
assert "OfferDistributionService" in source
assert "send_job_offers_to_carriers" in source
assert "manual_review_required" in source
assert "offers_exhausted" in source
assert "expired_without_response" in source
assert "no_carriers_found" in source
assert "redispatch_created, redispatch_sent = await redispatch_open_jobs_to_new_carrier" in source

print("CARRIER_APPROVAL_AUTO_REDISPATCH_SMOKE_OK")
