import asyncio
import os
import shutil
import subprocess
import sys
from datetime import UTC
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from app.bot.handlers.admin_controls import _resolve_client_target
from app.models.job import Job
from app.repositories.job import JobRepository

DATA_DIR = PROJECT_ROOT / ".tmp_client_ban_username_smoke"
DATABASE_URL = "sqlite+aiosqlite:///.tmp_client_ban_username_smoke/cargopt_dev.db"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def reset_db() -> None:
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(exist_ok=True)


async def exercise() -> None:
    engine = create_async_engine(DATABASE_URL)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)

    async with session_maker() as session:
        repo = JobRepository(session)
        await repo.create_job(
            Job(
                client_telegram_user_id=123456,
                client_telegram_username="SomeUser",
                status="draft",
                requested_date=None,
                assigned_at=None,
                started_at=None,
                completed_at=None,
                cancelled_at=None,
                client_confirmation_status=None,
                carrier_confirmation_status=None,
                needs_assembly=False,
                needs_packing=False,
                needs_tail_lift=False,
                needs_crane=False,
                needs_mobile_lift=False,
                required_loaders=None,
                estimated_payload_kg=None,
                estimated_volume_m3=None,
                comment=None,
                created_at=now,
                updated_at=now,
            )
        )

        assert await _resolve_client_target(repo, "123456") == (123456, None)
        assert await _resolve_client_target(repo, "@someuser") == (123456, "SomeUser")
        assert await _resolve_client_target(repo, "SomeUser") == (123456, "SomeUser")
        assert await _resolve_client_target(repo, "@missing") is None

        await session.commit()

    await engine.dispose()


def main() -> None:
    os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
    os.environ["DATABASE_URL"] = DATABASE_URL
    os.environ["ENVIRONMENT"] = "client-ban-username-smoke"
    os.environ["LOG_LEVEL"] = "INFO"

    reset_db()
    run([".venv/bin/alembic", "upgrade", "head"])
    asyncio.run(exercise())
    shutil.rmtree(DATA_DIR)

    print("CLIENT_BAN_USERNAME_SMOKE_OK")


if __name__ == "__main__":
    main()
