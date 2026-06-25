from pathlib import Path

source = Path("app/bot/handlers/job_media.py").read_text(encoding="utf-8")

assert "import asyncio" in source
assert "_MEDIA_ACK_LOCKS" in source
assert "message.media_group_id" in source
assert "async with _media_ack_lock(message):" in source
assert "if not data.get(\"media_ack_sent\"):" in source

print("MEDIA_ACK_ONCE_SMOKE_OK")
