import asyncio
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from app.repositories.job import JobRepository

DATA_DIR = PROJECT_ROOT / ".tmp_client_ban_repository_smoke"
DATABASE_URL = "sqlite+aiosqlite:///.tmp_client_ban_repository_smoke/cargopt_dev.db"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def reset_db() -> None:
    if DATA_DIR == PROJECT_ROOT / "data":
        raise RuntimeError("smoke must not delete PROJECT_ROOT/data")
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(exist_ok=True)


async def exercise() -> None:
    engine = create_async_engine(DATABASE_URL)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with session_maker() as session:
        repo = JobRepository(session)

        first = await repo.ban_client(
            telegram_user_id=123456,
            username="bad_client",
            reason="test reason",
            banned_by_admin_id=999,
        )
        second = await repo.ban_client(
            telegram_user_id=123456,
            username="bad_client",
            reason="duplicate",
            banned_by_admin_id=999,
        )

        if first.id != second.id:
            raise SystemExit("duplicate active ban was created")

        active = await repo.get_active_client_ban(123456)
        if active is None:
            raise SystemExit("active ban missing")

        unbanned = await repo.unban_client(
            telegram_user_id=123456,
            unbanned_by_admin_id=999,
        )
        if unbanned is None or unbanned.unbanned_at is None:
            raise SystemExit("ban was not unbanned")

        active_after = await repo.get_active_client_ban(123456)
        if active_after is not None:
            raise SystemExit("active ban still exists after unban")

        missing = await repo.unban_client(
            telegram_user_id=777777,
            unbanned_by_admin_id=999,
        )
        if missing is not None:
            raise SystemExit("missing unban must return None")

        await session.commit()

    await engine.dispose()


def main() -> None:
    os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
    os.environ["DATABASE_URL"] = DATABASE_URL
    os.environ["ENVIRONMENT"] = "client-ban-repository-smoke"
    os.environ["LOG_LEVEL"] = "INFO"

    reset_db()
    run([".venv/bin/alembic", "upgrade", "head"])
    asyncio.run(exercise())
    shutil.rmtree(DATA_DIR)

    print("CLIENT_BAN_REPOSITORY_SMOKE_OK")


if __name__ == "__main__":
    main()
