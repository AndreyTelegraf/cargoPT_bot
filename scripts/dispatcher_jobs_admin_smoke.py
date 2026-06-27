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
from app.bot.handlers.dispatcher_jobs_admin import dispatcher_jobs_attention
from app.bot.handlers.dispatcher_jobs_admin import dispatcher_jobs_report
from app.bot.handlers.dispatcher_jobs_admin import router
from app.repositories.job import JobRepository

assert router is not None
assert dispatcher_jobs is not None
assert dispatcher_jobs_attention is not None
assert dispatcher_jobs_report is not None
assert hasattr(JobRepository, "list_recent_jobs")
assert hasattr(JobRepository, "list_attention_jobs")

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
    attention_reason="price_not_agreed",
    offers_count=17,
)

line = _format_job_line(job)
assert _format_status("offered") == "отправлена перевозчикам"
assert _format_status("unmatched") == "перевозчик не найден"
assert _format_status("no_carriers_found") == "нет подходящих перевозчиков"
assert _format_status("offers_exhausted") == "все перевозчики отказались"
assert _format_status("expired_without_response") == "нет ответов от перевозчиков"
assert _format_status("manual_review_required") == "требует ручного контроля"
assert _format_status("assigned_pending_confirmation") == "ожидает подтверждения сделки"
assert _format_status("assigned") == "перевозчик назначен"
assert _format_status("unknown_status") == "unknown_status"
assert "<b>#42</b> — перевозчик назначен — @client_user" in line
assert "Дата: —" in line
assert "Назначена: —" in line
assert "Офферов: 17" in line
assert "Причина: Не договорились по цене" in line

router_source = Path("app/bot/routers.py").read_text(encoding="utf-8")
assert "dispatcher_jobs_admin_router" in router_source

handler_source = Path("app/bot/handlers/dispatcher_jobs_admin.py").read_text(encoding="utf-8")
assert 'Command("jobs")' in handler_source
assert 'Command("jobs_attention")' in handler_source
assert "ADMIN_TELEGRAM_USER_IDS" in handler_source
assert "list_recent_jobs(limit=20)" in handler_source
assert "list_attention_jobs(limit=20)" in handler_source
assert 'Command("jobs_report")' in handler_source
assert "CargoPT jobs report" in handler_source
assert "_format_report_job_rows" in handler_source
assert "get_decline_reason_label" in handler_source
assert "attention_reason" in handler_source
assert "offers_count" in handler_source

print("DISPATCHER_JOBS_ADMIN_SMOKE_OK")
