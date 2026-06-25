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

DATA_DIR = PROJECT_ROOT / ".tmp_carrier_target_resolver_smoke"
DATABASE_URL = "sqlite+aiosqlite:///.tmp_carrier_target_resolver_smoke/cargopt_dev.db"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def reset_db() -> None:
    if DATA_DIR == PROJECT_ROOT / "data":
        raise RuntimeError("smoke must not delete PROJECT_ROOT/data")
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(exist_ok=True)


async def exercise_resolver() -> None:
    engine = create_async_engine(DATABASE_URL)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)

    async with session_maker() as session:
        repo = CarrierRepository(session)

        by_company_name = await repo.create_carrier(
            CarrierCompany(
                company_name="@BusMovept",
                contact_name=None,
                phone=None,
                telegram_user_id=8447768984,
                telegram_username=None,
                status=CarrierStatus.ACTIVE,
                paid_until=None,
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

        by_username = await repo.create_carrier(
            CarrierCompany(
                company_name="Regular Carrier",
                contact_name=None,
                phone=None,
                telegram_user_id=1001,
                telegram_username="RegularUser",
                status=CarrierStatus.ACTIVE,
                paid_until=None,
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

        resolved_company = await repo.get_carrier_by_username("@BusMovept")
        if resolved_company is None:
            raise SystemExit("company-name @username fallback did not resolve")
        if resolved_company.id != by_company_name.id:
            raise SystemExit("company-name @username fallback resolved wrong carrier")

        resolved_username = await repo.get_carrier_by_username("@regularuser")
        if resolved_username is None:
            raise SystemExit("telegram_username resolver did not resolve")
        if resolved_username.id != by_username.id:
            raise SystemExit("telegram_username resolver resolved wrong carrier")

    await engine.dispose()


def main() -> None:
    os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
    os.environ["DATABASE_URL"] = DATABASE_URL
    os.environ["ENVIRONMENT"] = "carrier-target-resolver-smoke"
    os.environ["LOG_LEVEL"] = "INFO"

    reset_db()
    run([".venv/bin/alembic", "upgrade", "head"])
    asyncio.run(exercise_resolver())
    shutil.rmtree(DATA_DIR)

    print("CARRIER_TARGET_RESOLVER_SMOKE_OK")


if __name__ == "__main__":
    main()
