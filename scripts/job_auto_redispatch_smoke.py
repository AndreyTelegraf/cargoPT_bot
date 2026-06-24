from pathlib import Path

distribution_source = Path("app/services/offer_distribution.py").read_text(encoding="utf-8")
assignment_source = Path("app/services/assignment_confirmation.py").read_text(encoding="utf-8")
repo_source = Path("app/repositories/job.py").read_text(encoding="utf-8")

assert "list_offer_carrier_ids_by_job" in repo_source
assert "existing_carrier_ids = await self.job_repository.list_offer_carrier_ids_by_job(job.id)" in distribution_source
assert "if vehicle.carrier_id not in existing_carrier_ids" in distribution_source

assert "process_assignment_failure_redispatch" in assignment_source
assert "send_job_offers_to_carriers" in assignment_source
assert "build_assignment_offer_distribution" in assignment_source
assert "should_delete_carrier_offer" in assignment_source

print("JOB_AUTO_REDISPATCH_SMOKE_OK")
