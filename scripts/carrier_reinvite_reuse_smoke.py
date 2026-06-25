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

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.domain.carrier_status import CarrierStatus
from app.models.carrier import CarrierCompany
from app.repositories.carrier import CarrierRepository
from app.services.carrier_onboarding import CarrierOnboardingService

DATA_DIR = PROJECT_ROOT / ".tmp_carrier_reinvite_reuse_smoke"
DATABASE_URL = "sqlite+aiosqlite:///.tmp_carrier_reinvite_reuse_smoke/cargopt_dev.db"

def run(cmd):
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)

def reset_db():
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(exist_ok=True)

async def exercise():
    engine = create_async_engine(DATABASE_URL)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)

    async with session_maker() as session:
        repo = CarrierRepository(session)
        service = CarrierOnboardingService(repo)

        carrier = await repo.create_carrier(
            CarrierCompany(
                company_name="@duplicate",
                contact_name="Old Contact",
                phone="+351000000000",
                telegram_user_id=123,
                telegram_username="duplicate",
                status=CarrierStatus.PENDING_MODERATION,
                paid_until=now,
                assembly_required=True,
                packing_required=True,
                operating_regions="Lisboa",
                profile_completed_at=now,
                current_profile_step="completed",
                internal_note="old",
                created_at=now,
                updated_at=now,
            )
        )

        found = await repo.get_latest_carrier_by_company_name("@duplicate")
        assert found is not None
        assert found.id == carrier.id

        reset = await service.reuse_carrier_for_reinvite(carrier_id=carrier.id)
        invite = await service.create_invite_token(
            carrier_id=reset.id,
            created_by_admin_id=336224597,
            expires_in_days=30,
        )

        await session.commit()

        again = await repo.get_carrier_by_id(carrier.id)
        assert again is not None
        assert again.id == carrier.id
        assert again.telegram_user_id is None
        assert again.telegram_username is None
        assert again.status == CarrierStatus.INVITED
        assert again.current_profile_step is None
        assert again.profile_completed_at is None
        assert again.operating_regions is None
        assert invite.carrier_id == carrier.id

    await engine.dispose()

def main():
    os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
    os.environ["DATABASE_URL"] = DATABASE_URL
    os.environ["ENVIRONMENT"] = "carrier-reinvite-reuse-smoke"
    os.environ["LOG_LEVEL"] = "INFO"

    reset_db()
    run([".venv/bin/alembic", "upgrade", "head"])
    asyncio.run(exercise())
    shutil.rmtree(DATA_DIR)

    print("CARRIER_REINVITE_REUSE_SMOKE_OK")

if __name__ == "__main__":
    main()
