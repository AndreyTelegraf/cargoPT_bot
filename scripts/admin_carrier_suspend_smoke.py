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

DATA_DIR = PROJECT_ROOT / ".tmp_admin_carrier_suspend_smoke"
DATABASE_URL = "sqlite+aiosqlite:///.tmp_admin_carrier_suspend_smoke/cargopt_dev.db"


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
        repo = CarrierRepository(session)

        carrier = await repo.create_carrier(
            CarrierCompany(
                company_name="Suspend Carrier",
                contact_name=None,
                phone=None,
                telegram_user_id=123456,
                status=CarrierStatus.ACTIVE,
                paid_until=None,
                assembly_required=False,
                packing_required=False,
                operating_regions="Lisboa",
                profile_completed_at=now,
                current_profile_step=None,
                internal_note=None,
                created_at=now,
                updated_at=now,
            )
        )

        suspended = await repo.suspend_carrier(carrier.id)
        if suspended.status != CarrierStatus.SUSPENDED:
            raise SystemExit(f"unexpected suspended status: {suspended.status}")

        restored = await repo.unsuspend_carrier(carrier.id)
        if restored.status != CarrierStatus.ACTIVE:
            raise SystemExit(f"unexpected restored status: {restored.status}")

        await session.commit()

    await engine.dispose()


def main() -> None:
    os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
    os.environ["DATABASE_URL"] = DATABASE_URL
    os.environ["ENVIRONMENT"] = "admin-carrier-suspend-smoke"
    os.environ["LOG_LEVEL"] = "INFO"

    status_source = Path("app/domain/carrier_status.py").read_text(encoding="utf-8")
    repo_source = Path("app/repositories/carrier.py").read_text(encoding="utf-8")
    admin_source = Path("app/bot/handlers/admin_controls.py").read_text(encoding="utf-8")

    assert 'SUSPENDED = "suspended"' in status_source
    assert "async def suspend_carrier(" in repo_source
    assert "async def unsuspend_carrier(" in repo_source
    assert 'Command("suspend_carrier")' in admin_source
    assert 'Command("unsuspend_carrier")' in admin_source

    reset_db()
    run([".venv/bin/alembic", "upgrade", "head"])
    asyncio.run(exercise())
    shutil.rmtree(DATA_DIR)

    print("ADMIN_CARRIER_SUSPEND_SMOKE_OK")


if __name__ == "__main__":
    main()
