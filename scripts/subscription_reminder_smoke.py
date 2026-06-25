import asyncio
import os
import shutil
import subprocess
import sys
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from app.domain.carrier_status import CarrierStatus
from app.models.carrier import CarrierCompany
from app.repositories.carrier import CarrierRepository
from app.services.subscription_reminder import process_subscription_reminders

DATA_DIR = PROJECT_ROOT / ".tmp_subscription_reminder_smoke"
DATABASE_URL = "sqlite+aiosqlite:///.tmp_subscription_reminder_smoke/cargopt_dev.db"


class DummyBot:
    def __init__(self):
        self.messages = []

    async def send_message(self, *, chat_id, text):
        self.messages.append((chat_id, text))


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def reset_db() -> None:
    if DATA_DIR == PROJECT_ROOT / "data":
        raise RuntimeError("smoke must not delete PROJECT_ROOT/data")
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(exist_ok=True)


async def exercise_reminder() -> None:
    engine = create_async_engine(DATABASE_URL)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)

    async with session_maker() as session:
        repo = CarrierRepository(session)

        carrier = await repo.create_carrier(
            CarrierCompany(
                company_name="Reminder Carrier",
                contact_name=None,
                phone=None,
                telegram_user_id=777001,
                telegram_username="reminder_carrier",
                status=CarrierStatus.ACTIVE,
                paid_until=now + timedelta(days=3),
                assembly_required=False,
                packing_required=False,
                operating_regions=None,
                profile_completed_at=None,
                current_profile_step=None,
                internal_note=None,
                created_at=now,
                updated_at=now,
            )
        )

        await session.commit()

        bot = DummyBot()
        sent = await process_subscription_reminders(
            bot=bot,
            session=session,
        )
        await session.commit()

        if sent != 1:
            raise SystemExit(f"expected 1 sent reminder, got {sent}")
        if len(bot.messages) != 1:
            raise SystemExit(f"expected 1 bot message, got {len(bot.messages)}")
        if bot.messages[0][0] != 777001:
            raise SystemExit("message sent to wrong chat")
        if "действует до" not in bot.messages[0][1]:
            raise SystemExit("unexpected reminder text")

        loaded = await repo.get_carrier_by_id(carrier.id)
        if "[subscription_reminder:" not in (loaded.internal_note or ""):
            raise SystemExit("reminder marker was not stored")

        second_bot = DummyBot()
        sent_again = await process_subscription_reminders(
            bot=second_bot,
            session=session,
        )
        await session.commit()

        if sent_again != 0:
            raise SystemExit(f"expected no duplicate reminder, got {sent_again}")
        if second_bot.messages:
            raise SystemExit("duplicate bot message was sent")

    await engine.dispose()


def main() -> None:
    os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
    os.environ["DATABASE_URL"] = DATABASE_URL
    os.environ["ENVIRONMENT"] = "subscription-reminder-smoke"
    os.environ["LOG_LEVEL"] = "INFO"

    reset_db()
    run([".venv/bin/alembic", "upgrade", "head"])
    asyncio.run(exercise_reminder())
    shutil.rmtree(DATA_DIR)

    print("SUBSCRIPTION_REMINDER_SMOKE_OK")


if __name__ == "__main__":
    main()
