from pathlib import Path

source = Path("app/bot/handlers/job_assignment_confirmation.py").read_text(encoding="utf-8")

assert "except TelegramBadRequest:" in source
assert "await callback.message.edit_reply_markup(reply_markup=None)" in source
assert "pass" in source

print("JOB_ASSIGNMENT_CONFIRMATION_HANDLER_SMOKE_OK")
