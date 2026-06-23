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

from app.domain.job_status import JobStatus
from app.repositories.job import JobRepository
from app.services.job import JobService
from app.services.job import InvalidJobStatusTransitionError
from app.services.job import cancel_job
from app.services.job import complete_job
from app.services.job import start_job

DATA_DIR = PROJECT_ROOT / ".tmp_job_lifecycle_smoke"
DATABASE_URL = "sqlite+aiosqlite:///.tmp_job_lifecycle_smoke/cargopt_dev.db"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def reset_db() -> None:
    if DATA_DIR == PROJECT_ROOT / "data":
        raise RuntimeError("smoke must not delete PROJECT_ROOT/data")
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(exist_ok=True)


async def exercise_lifecycle() -> None:
    engine = create_async_engine(DATABASE_URL)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with session_maker() as session:
        repo = JobRepository(session)
        service = JobService(repo)

        job = await service.create_draft_job(
            client_telegram_user_id=9001,
            client_telegram_username="client_user",
        )
        await session.commit()

        assigned = await repo.update_job_status(
            job_id=job.id,
            status=JobStatus.ASSIGNED,
            updated_at=job.updated_at,
        )
        await session.commit()

        if assigned.assigned_at is None:
            raise SystemExit("assigned_at missing after assigned")

        started = await start_job(service, job_id=job.id)
        await session.commit()

        if started.status != JobStatus.IN_PROGRESS:
            raise SystemExit(f"unexpected started status: {started.status}")
        if started.started_at is None:
            raise SystemExit("started_at missing")

        completed = await complete_job(service, job_id=job.id)
        await session.commit()

        if completed.status != JobStatus.COMPLETED:
            raise SystemExit(f"unexpected completed status: {completed.status}")
        if completed.completed_at is None:
            raise SystemExit("completed_at missing")

        try:
            await start_job(service, job_id=job.id)
        except InvalidJobStatusTransitionError:
            pass
        else:
            raise SystemExit("invalid restart unexpectedly succeeded")

        cancel_target = await service.create_draft_job(
            client_telegram_user_id=9002,
            client_telegram_username="cancel_user",
        )
        await repo.update_job_status(
            job_id=cancel_target.id,
            status=JobStatus.ASSIGNED,
            updated_at=cancel_target.updated_at,
        )
        cancelled = await cancel_job(service, job_id=cancel_target.id)
        await session.commit()

        if cancelled.status != JobStatus.CANCELLED:
            raise SystemExit(f"unexpected cancelled status: {cancelled.status}")
        if cancelled.cancelled_at is None:
            raise SystemExit("cancelled_at missing")

    await engine.dispose()


def main() -> None:
    os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
    os.environ["DATABASE_URL"] = DATABASE_URL
    os.environ["ENVIRONMENT"] = "job-lifecycle-smoke"
    os.environ["LOG_LEVEL"] = "INFO"

    reset_db()
    run([".venv/bin/alembic", "upgrade", "head"])
    asyncio.run(exercise_lifecycle())
    shutil.rmtree(DATA_DIR)

    print("JOB_LIFECYCLE_SMOKE_OK")


if __name__ == "__main__":
    main()
