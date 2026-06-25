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

from app.domain.carrier_status import CarrierStatus
from app.models.carrier import CarrierCompany
from app.repositories.carrier import CarrierRepository

DATA_DIR = PROJECT_ROOT / ".tmp_carrier_duplicate_username_resolver_smoke"
DATABASE_URL = "sqlite+aiosqlite:///.tmp_carrier_duplicate_username_resolver_smoke/cargopt_dev.db"


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
    now = datetime.now(UTC)

    async with session_maker() as session:
        repo = CarrierRepository(session)

        old = await repo.create_carrier(
            CarrierCompany(
                company_name="@vasylkuzyshyn",
                contact_name=None,
                phone=None,
                telegram_user_id=None,
                telegram_username=None,
                status=CarrierStatus.REJECTED,
                paid_until=None,
                assembly_required=False,
                packing_required=False,
                operating_regions=None,
                profile_completed_at=None,
                current_profile_step="reset_for_reinvite",
                internal_note=None,
                created_at=now,
                updated_at=now,
            )
        )

        active = await repo.create_carrier(
            CarrierCompany(
                company_name="@vasylkuzyshyn",
                contact_name=None,
                phone=None,
                telegram_user_id=5403730444,
                telegram_username=None,
                status=CarrierStatus.ACTIVE,
                paid_until=None,
                assembly_required=False,
                packing_required=False,
                operating_regions=None,
                profile_completed_at=now,
                current_profile_step="completed",
                internal_note=None,
                created_at=now,
                updated_at=now,
            )
        )

        await session.commit()

        resolved = await repo.get_carrier_by_username("@vasylkuzyshyn")
        if resolved is None:
            raise SystemExit("expected active carrier, got None")
        if resolved.id != active.id:
            raise SystemExit(f"expected active id {active.id}, got {resolved.id}")
        if resolved.id == old.id:
            raise SystemExit("resolved rejected old carrier")

    await engine.dispose()


def main() -> None:
    os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
    os.environ["DATABASE_URL"] = DATABASE_URL
    os.environ["ENVIRONMENT"] = "carrier-duplicate-username-resolver-smoke"
    os.environ["LOG_LEVEL"] = "INFO"

    reset_db()
    run([".venv/bin/alembic", "upgrade", "head"])
    asyncio.run(exercise())
    shutil.rmtree(DATA_DIR)

    print("CARRIER_DUPLICATE_USERNAME_RESOLVER_SMOKE_OK")


if __name__ == "__main__":
    main()
