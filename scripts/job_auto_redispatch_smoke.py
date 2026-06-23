from pathlib import Path

distribution_source = Path("app/services/offer_distribution.py").read_text(encoding="utf-8")
handler_source = Path("app/bot/handlers/job_assignment_confirmation.py").read_text(encoding="utf-8")
repo_source = Path("app/repositories/job.py").read_text(encoding="utf-8")

assert "list_offer_carrier_ids_by_job" in repo_source
assert "existing_carrier_ids = await self.job_repository.list_offer_carrier_ids_by_job(job.id)" in distribution_source
assert "if vehicle.carrier_id not in existing_carrier_ids" in distribution_source
assert "send_job_offers_to_carriers" in handler_source
assert "OfferDistributionService" in handler_source
assert "should_delete_carrier_offer" in handler_source

print("JOB_AUTO_REDISPATCH_SMOKE_OK")
