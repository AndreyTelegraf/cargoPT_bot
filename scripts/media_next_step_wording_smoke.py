from pathlib import Path

keyboard = Path("app/bot/job_request_keyboards.py").read_text()
media = Path("app/bot/handlers/job_media.py").read_text()

assert "Следующий шаг" in keyboard
assert "Следующий шаг" in media
assert "Пропустить медиа" in media  # backward-compatible old button text
assert "Пропустить медиа" not in keyboard

print("MEDIA_NEXT_STEP_WORDING_SMOKE_OK")
