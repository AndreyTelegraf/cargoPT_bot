import os
import sys
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

from app.bot.handlers.dispatcher_jobs_admin import _format_job_line
from app.bot.handlers.dispatcher_jobs_admin import _format_status
from app.bot.handlers.dispatcher_jobs_admin import dispatcher_jobs
from app.bot.handlers.dispatcher_jobs_admin import router
from app.repositories.job import JobRepository

assert router is not None
assert dispatcher_jobs is not None
assert hasattr(JobRepository, "list_recent_jobs")

job = SimpleNamespace(
    id=42,
    status="assigned",
    client_telegram_username="client_user",
    client_telegram_user_id=987654321,
    requested_date=None,
    assigned_at=None,
    started_at=None,
    completed_at=None,
    cancelled_at=None,
)

line = _format_job_line(job)
assert _format_status("offered") == "отправлена перевозчикам"
assert _format_status("unmatched") == "перевозчик не найден"
assert _format_status("assigned_pending_confirmation") == "ожидает подтверждения сделки"
assert _format_status("assigned") == "перевозчик назначен"
assert _format_status("unknown_status") == "unknown_status"
assert "<b>#42</b> — перевозчик назначен — @client_user" in line
assert "Дата: —" in line
assert "Назначена: —" in line

router_source = Path("app/bot/routers.py").read_text(encoding="utf-8")
assert "dispatcher_jobs_admin_router" in router_source

handler_source = Path("app/bot/handlers/dispatcher_jobs_admin.py").read_text(encoding="utf-8")
assert 'Command("jobs")' in handler_source
assert "ADMIN_TELEGRAM_USER_IDS" in handler_source
assert "list_recent_jobs(limit=20)" in handler_source

print("DISPATCHER_JOBS_ADMIN_SMOKE_OK")
