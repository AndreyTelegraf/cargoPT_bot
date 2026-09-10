import asyncio
import os
import sys
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("BOT_TOKEN", "123456:TESTTOKEN")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///data/cargopt_dev.db")

from app.bot.handlers.job_offer_response import _prompt_offer_price
from app.bot.offer_keyboard import build_offer_decline_reason_keyboard


class FakeState:
    def __init__(self):
        self.data = {}

    async def clear(self):
        self.data = {}

    async def update_data(self, **kwargs):
        self.data.update(kwargs)

    async def set_state(self, value):
        self.state = value


class FakeMessage:
    chat = SimpleNamespace(id=10)
    message_id = 20

    def __init__(self):
        self.answers = []

    async def answer(self, text, **kwargs):
        self.answers.append(text)


class FakeCallback:
    def __init__(self):
        self.message = FakeMessage()
        self.answers = []

    async def answer(self, text, **kwargs):
        self.answers.append(text)


async def main() -> None:
    callback = FakeCallback()
    state = FakeState()
    await _prompt_offer_price(callback, state, 7, locale="pt")
    assert state.data["offer_price_locale"] == "pt"
    assert callback.message.answers[0].startswith("Responda com o preço")
    assert callback.answers == ["Envie o preço numa mensagem de resposta."]

    pt_reasons = build_offer_decline_reason_keyboard(7, locale="pt")
    en_reasons = build_offer_decline_reason_keyboard(7, locale="en")
    ru_reasons = build_offer_decline_reason_keyboard(7, locale="ru")
    assert pt_reasons.inline_keyboard[0][0].text == "Horário indisponível"
    assert en_reasons.inline_keyboard[0][0].text == "Time unavailable"
    assert ru_reasons.inline_keyboard[0][0].text == "Не подошло время"

    print("JOB_OFFER_LOCALE_SMOKE_OK")


if __name__ == "__main__":
    asyncio.run(main())
