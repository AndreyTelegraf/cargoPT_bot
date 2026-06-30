from pathlib import Path

source = Path("app/bot/handlers/job_assignment_confirmation.py").read_text(encoding="utf-8")
handler = source[source.index("async def handle_assignment_confirmation"):]

assert "await callback.message.edit_text(result_text, reply_markup=None)" in handler
assert "await callback.message.edit_reply_markup(reply_markup=None)" in handler
assert "await callback.answer(result_text, show_alert=True)" in handler

print("ASSIGNMENT_CONFIRMATION_MESSAGE_CLEANUP_SMOKE_OK")
