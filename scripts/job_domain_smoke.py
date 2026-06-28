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

from datetime import UTC
from datetime import datetime

from app.domain.job_status import JobStatus
from app.models.job import Job
from app.models.job import JobAddress
from app.models.job import JobItem
from app.repositories.job import JobRepository

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
        now = datetime.now(UTC)

        job = await repo.create_job(
            Job(
                client_telegram_user_id=777000111,
                status=JobStatus.DRAFT,
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
                comment="Need transport",
                created_at=now,
                updated_at=now,
            )
        )

        if job.id is None:
            raise SystemExit("job id missing")

        await repo.add_address(
            JobAddress(
                job_id=job.id,
                kind="pickup",
                raw_text="Lisboa",
                normalized_address="Lisboa",
                created_at=now,
            )
        )

        await repo.add_address(
            JobAddress(
                job_id=job.id,
                kind="dropoff",
                raw_text="Porto",
                normalized_address="Porto",
                created_at=now,
            )
        )

        await repo.add_item(
            JobItem(
                job_id=job.id,
                description="Boxes",
                quantity=10,
                estimated_weight_kg=None,
                estimated_volume_m3=None,
                created_at=now,
            )
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
