import asyncio
import os
import shutil
import subprocess
import sys
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from app.models.carrier import AdminInviteToken
from app.models.carrier import CarrierCompany
from app.models.carrier import CarrierVehicle
from app.repositories.carrier import CarrierRepository


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "cargopt_dev.db"
DATABASE_URL = "sqlite+aiosqlite:///data/cargopt_dev.db"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def reset_db() -> None:
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(exist_ok=True)


async def exercise_repository() -> None:
    engine = create_async_engine(DATABASE_URL)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    now = datetime.now(UTC)

    async with session_maker() as session:
        repo = CarrierRepository(session)

        carrier = await repo.create_carrier(
            CarrierCompany(
                company_name="Smoke Carrier",
                contact_name="Smoke Contact",
                phone="+351900000000",
                telegram_user_id=900000001,
                status="draft",
                paid_until=now + timedelta(days=30),
                internal_note="repository smoke",
                created_at=now,
                updated_at=now,
            )
        )

        invite = await repo.create_invite_token(
            AdminInviteToken(
                token="repo-smoke-token",
                carrier_id=carrier.id,
                created_by_admin_id=1001,
                expires_at=now + timedelta(days=7),
                used_at=None,
                used_by_telegram_id=None,
                status="active",
                created_at=now,
            )
        )

        session.add(
            CarrierVehicle(
                carrier_id=carrier.id,
                vehicle_type="medium_van",
                payload_kg=1200,
                volume_m3=12.5,
                has_tail_lift=True,
                has_crane=False,
                has_mobile_lift=False,
                mobile_lift_max_floor=None,
                mobile_lift_max_weight_kg=None,
                crane_max_weight_kg=None,
                crane_reach_meters=None,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        )

        await session.commit()

    async with session_maker() as session:
        repo = CarrierRepository(session)

        carrier_by_id = await repo.get_carrier_by_id(1)
        if carrier_by_id is None:
            raise SystemExit("carrier_by_id missing")
        if carrier_by_id.company_name != "Smoke Carrier":
            raise SystemExit("carrier_by_id mismatch")

        carrier_by_tg = await repo.get_carrier_by_telegram_user_id(900000001)
        if carrier_by_tg is None:
            raise SystemExit("carrier_by_tg missing")
        if carrier_by_tg.id != carrier_by_id.id:
            raise SystemExit("carrier_by_tg id mismatch")

        invite_by_token = await repo.get_invite_token(invite.token)
        if invite_by_token is None:
            raise SystemExit("invite_by_token missing")
        if invite_by_token.carrier_id != carrier_by_id.id:
            raise SystemExit("invite carrier mismatch")

        vehicles = await repo.list_vehicles_by_carrier(carrier_by_id.id)
        if len(vehicles) != 1:
            raise SystemExit(f"expected 1 vehicle, got {len(vehicles)}")
        if vehicles[0].vehicle_type != "medium_van":
            raise SystemExit("vehicle_type mismatch")

    await engine.dispose()


def main() -> None:
    os.environ["BOT_TOKEN"] = "carrier-repo-smoke-token"
    os.environ["DATABASE_URL"] = DATABASE_URL
    os.environ["ENVIRONMENT"] = "carrier-repository-smoke"
    os.environ["LOG_LEVEL"] = "INFO"

    reset_db()
    run([".venv/bin/alembic", "upgrade", "head"])

    asyncio.run(exercise_repository())

    shutil.rmtree(DATA_DIR)

    print("CARRIER_REPOSITORY_SMOKE_OK")


if __name__ == "__main__":
    main()
