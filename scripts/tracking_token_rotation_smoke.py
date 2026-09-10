import asyncio
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
DATA_DIR = PROJECT_ROOT / ".tmp_tracking_token_rotation_smoke"
DATABASE_URL = (
    "sqlite+aiosqlite:///.tmp_tracking_token_rotation_smoke/cargopt.db"
)


def prepare_database() -> None:
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir()
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=PROJECT_ROOT,
        env=os.environ.copy(),
        check=True,
    )


async def exercise_rotation() -> None:
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.domain.job_status import JobStatus
    from app.models.job import Job
    from app.repositories.job import JobRepository

    engine = create_async_engine(DATABASE_URL)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)

    async with session_maker() as session:
        repository = JobRepository(session)
        job = await repository.create_job(
            Job(
                status=JobStatus.DRAFT,
                source_locale="en",
                created_at=now,
                updated_at=now,
            )
        )
        await session.commit()
        old_token = job.tracking_token

        rotated = await repository.rotate_tracking_token(job.id, updated_at=now)
        await session.commit()
        new_token = rotated.tracking_token

        assert old_token
        assert new_token
        assert new_token != old_token
        assert await repository.get_job_by_tracking_token(old_token) is None
        assert (
            await repository.get_job_by_tracking_token(new_token)
        ).id == job.id

    await engine.dispose()


def main() -> None:
    os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
    os.environ["DATABASE_URL"] = DATABASE_URL
    os.environ["ENVIRONMENT"] = "tracking-token-rotation-smoke"
    prepare_database()
    asyncio.run(exercise_rotation())

    from app.api.main import app

    assert "/api/v1/track/{tracking_token}/rotate" in app.openapi()["paths"]
    shutil.rmtree(DATA_DIR)
    print("TRACKING_TOKEN_ROTATION_SMOKE_OK")


if __name__ == "__main__":
    main()
