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
from app.domain.job_offer_status import JobOfferStatus
from app.domain.job_status import JobStatus
from app.models.carrier import CarrierCompany
from app.models.carrier import CarrierVehicle
from app.models.job import Job
from app.repositories.carrier import CarrierRepository
from app.repositories.job import JobRepository
from app.services.job_offer import JobOfferService

DATA_DIR = PROJECT_ROOT / ".tmp_job_assignment_smoke"
DATABASE_URL = "sqlite+aiosqlite:///.tmp_job_assignment_smoke/cargopt_dev.db"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def reset_db() -> None:
    if DATA_DIR == PROJECT_ROOT / "data":
        raise RuntimeError("smoke must not delete PROJECT_ROOT/data")
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(exist_ok=True)


async def exercise_job_assignment() -> None:
    engine = create_async_engine(DATABASE_URL)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)

    async with session_maker() as session:
        carrier_repo = CarrierRepository(session)
        job_repo = JobRepository(session)

        carrier = await carrier_repo.create_carrier(
            CarrierCompany(
                company_name="Assign Carrier",
                contact_name=None,
                phone=None,
                telegram_user_id=6001,
                status=CarrierStatus.PROFILE_COMPLETED,
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

        vehicle = await carrier_repo.create_vehicle(
            CarrierVehicle(
                carrier_id=carrier.id,
                vehicle_type="large_van",
                payload_kg=1600,
                volume_m3=18.0,
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

        job = await job_repo.create_job(
            Job(
                client_telegram_user_id=9001,
                status=JobStatus.MATCHING,
                requested_date=None,
                needs_assembly=False,
                needs_packing=False,
                needs_tail_lift=True,
                needs_crane=False,
                needs_mobile_lift=False,
                required_loaders=None,
                estimated_payload_kg=1000,
                estimated_volume_m3=12.0,
                comment=None,
                created_at=now,
                updated_at=now,
            )
        )

        service = JobOfferService(job_repo)

        second_carrier = await carrier_repo.create_carrier(
            CarrierCompany(
                company_name="Second Assign Carrier",
                contact_name=None,
                phone=None,
                telegram_user_id=6002,
                status=CarrierStatus.PROFILE_COMPLETED,
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

        second_vehicle = await carrier_repo.create_vehicle(
            CarrierVehicle(
                carrier_id=second_carrier.id,
                vehicle_type="large_van",
                payload_kg=1600,
                volume_m3=18.0,
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

        offer = await service.create_offer(
            job_id=job.id,
            vehicle=vehicle,
            expires_in_minutes=30,
        )

        second_offer = await service.create_offer(
            job_id=job.id,
            vehicle=second_vehicle,
            expires_in_minutes=30,
        )

        accepted = await service.accept_offer_and_assign_job(offer.id)

        await session.commit()

        loaded_job = await job_repo.get_job_by_id(job.id)
        loaded_second_offer = await job_repo.get_offer_by_id(second_offer.id)

        if accepted.status != JobOfferStatus.ACCEPTED:
            raise SystemExit(f"unexpected offer status: {accepted.status}")

        if loaded_second_offer.status != JobOfferStatus.DECLINED:
            raise SystemExit(f"unexpected sibling offer status: {loaded_second_offer.status}")

        if loaded_second_offer.responded_at is None:
            raise SystemExit("sibling offer responded_at missing")

        if loaded_job.status != JobStatus.ASSIGNED:
            raise SystemExit(f"unexpected job status: {loaded_job.status}")

        try:
            await service.accept_offer_and_assign_job(offer.id)
        except Exception as exc:
            if exc.__class__.__name__ != "OfferAlreadyResolvedError":
                raise
        else:
            raise SystemExit("second accept unexpectedly succeeded")

    await engine.dispose()


def main() -> None:
    os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
    os.environ["DATABASE_URL"] = DATABASE_URL
    os.environ["ENVIRONMENT"] = "job-assignment-smoke"
    os.environ["LOG_LEVEL"] = "INFO"

    reset_db()
    run([".venv/bin/alembic", "upgrade", "head"])
    asyncio.run(exercise_job_assignment())
    shutil.rmtree(DATA_DIR)

    print("JOB_ASSIGNMENT_SMOKE_OK")


if __name__ == "__main__":
    main()
