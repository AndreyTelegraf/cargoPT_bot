import json
from asyncio import Lock
from pathlib import Path
from typing import Any

from app.config import settings

SELF_AD_TEXT = """🚚 <b>Нужно перевезти мебель, вещи или технику?</b>

Заполните заявку через <a href="https://t.me/cargo_pt_bot">@cargo_pt_bot</a>.

Агрегатор автоматически разошлёт заявку подходящим под ваш заказ перевозчикам."""

_lock = Lock()


def _state_path() -> Path:
    return Path(settings.self_ad_state_path)


def _load_count() -> int:
    path = _state_path()
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return 0
    value = data.get("text_count", 0)
    return value if isinstance(value, int) and value >= 0 else 0


def _save_count(count: int) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"text_count": count}, ensure_ascii=False, indent=2))


def is_target_text_message(message: Any) -> bool:
    if not settings.self_ad_enabled:
        return False

    text = getattr(message, "text", None)
    if not isinstance(text, str) or not text.strip():
        return False

    if text.strip() == SELF_AD_TEXT.strip():
        return False

    thread_id = getattr(message, "message_thread_id", None)
    if thread_id != settings.self_ad_topic_id:
        return False

    chat = getattr(message, "chat", None)
    username = getattr(chat, "username", None)
    if isinstance(username, str) and username.lower() == settings.self_ad_chat_username.lower():
        return True

    return False


async def process_self_ad_message(message: Any) -> bool:
    if not is_target_text_message(message):
        return False

    async with _lock:
        count = _load_count() + 1
        should_post = count % settings.self_ad_every_n == 0
        _save_count(count)

    if should_post:
        await message.answer(SELF_AD_TEXT)

    return should_post
