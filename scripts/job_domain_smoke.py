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
from app.services.job import JobService

DATA_DIR = PROJECT_ROOT / "data"
DATABASE_URL = "sqlite+aiosqlite:///data/cargopt_dev.db"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def reset_db() -> None:
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(exist_ok=True)


async def exercise_job_domain() -> None:
    engine = create_async_engine(DATABASE_URL)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with session_maker() as session:
        repo = JobRepository(session)
        service = JobService(repo)

        job = await service.create_draft_job(
            client_telegram_user_id=777000111,
            comment="Need transport",
        )

        if job.id is None:
            raise SystemExit("job id missing")

        await service.add_address(
            job_id=job.id,
            kind="pickup",
            raw_text="Lisboa",
        )

        await service.add_address(
            job_id=job.id,
            kind="dropoff",
            raw_text="Porto",
        )

        await service.add_item(
            job_id=job.id,
            description="Boxes",
            quantity=10,
        )

        await session.commit()

        loaded = await repo.get_job_by_id(job.id)

        if loaded is None:
            raise SystemExit("job not loaded")

    await engine.dispose()


def main() -> None:
    os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
    os.environ["DATABASE_URL"] = DATABASE_URL
    os.environ["ENVIRONMENT"] = "job-domain-smoke"
    os.environ["LOG_LEVEL"] = "INFO"

    reset_db()
    run([".venv/bin/alembic", "upgrade", "head"])
    asyncio.run(exercise_job_domain())
    shutil.rmtree(DATA_DIR)

    print("JOB_DOMAIN_SMOKE_OK")


if __name__ == "__main__":
    main()
