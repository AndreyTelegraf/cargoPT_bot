from pathlib import Path

repo = Path("app/repositories/job.py").read_text(encoding="utf-8")
handler = Path("app/bot/handlers/job_comment.py").read_text(encoding="utf-8")

assert "count_active_client_jobs" in repo
assert "count_sent_client_jobs_since" in repo
assert "\"no_carriers_found\"" not in repo[repo.index("async def count_sent_client_jobs_since"):repo.index("async def list_recent_jobs")]
assert "\"offers_exhausted\"" in repo
assert "\"expired_without_response\"" in repo
assert "\"manual_review_required\"" in repo

assert "active_jobs >= 2" in handler
assert "sent_jobs >= 3" in handler
assert "timedelta(hours=24)" in handler
assert "finalize_for_matching" in handler
assert "escalate_job_to_manual_review" in handler
assert "if not offers:" in handler

print("CLIENT_JOB_RATE_LIMIT_SMOKE_OK")
