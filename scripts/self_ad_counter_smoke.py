import asyncio
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.services import self_ad_counter


class FakeMessage:
    def __init__(self, *, text="hello", topic_id=429, username="baraholka_pt", is_bot=False):
        self.text = text
        self.message_thread_id = topic_id
        self.chat = SimpleNamespace(username=username)
        self.from_user = SimpleNamespace(is_bot=is_bot)
        self.sent = []

    async def answer(self, text):
        self.sent.append(text)


async def main():
    with tempfile.TemporaryDirectory() as tmp:
        old_path = settings.self_ad_state_path
        settings.self_ad_state_path = str(Path(tmp) / "self_ad_counter.json")
        try:
            sent = 0
            for _ in range(8):
                msg = FakeMessage()
                posted = await self_ad_counter.process_self_ad_message(msg)
                assert posted is False
                assert msg.sent == []

            msg = FakeMessage()
            posted = await self_ad_counter.process_self_ad_message(msg)
            assert posted is True
            assert len(msg.sent) == 1
            sent += len(msg.sent)

            wrong_topic = FakeMessage(topic_id=430)
            posted = await self_ad_counter.process_self_ad_message(wrong_topic)
            assert posted is False
            assert wrong_topic.sent == []

            channel_sender_message = FakeMessage(is_bot=True)
            posted = await self_ad_counter.process_self_ad_message(channel_sender_message)
            assert posted is False
            assert channel_sender_message.sent == []

            own_ad_message = FakeMessage(text=self_ad_counter.SELF_AD_TEXT)
            posted = await self_ad_counter.process_self_ad_message(own_ad_message)
            assert posted is False
            assert own_ad_message.sent == []

            assert sent == 1
        finally:
            settings.self_ad_state_path = old_path

    print("SELF_AD_COUNTER_SMOKE_OK")


asyncio.run(main())
