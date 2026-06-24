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
from app.domain.job_status import JobStatus
from app.models.carrier import CarrierCompany
from app.models.carrier import CarrierVehicle
from app.models.job import Job
from app.repositories.carrier import CarrierRepository
from app.repositories.job import JobRepository
from app.services.carrier_search import CarrierSearchService
from app.services.job_matching import JobMatchingService
from app.services.job_offer import JobOfferService
from app.services.offer_distribution import OfferDistributionService

DATA_DIR = PROJECT_ROOT / ".tmp_offer_distribution_smoke"
DATABASE_URL = "sqlite+aiosqlite:///.tmp_offer_distribution_smoke/cargopt_dev.db"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def reset_db() -> None:
    if DATA_DIR == PROJECT_ROOT / "data":
        raise RuntimeError("smoke must not delete PROJECT_ROOT/data")
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(exist_ok=True)


def build_job(now, *, payload: int, volume: float) -> Job:
    return Job(
        client_telegram_user_id=9001,
        status=JobStatus.READY_FOR_MATCHING,
        requested_date=None,
        assigned_at=None,
        started_at=None,
        completed_at=None,
        cancelled_at=None,
        needs_assembly=True,
        needs_packing=True,
        needs_tail_lift=True,
        needs_crane=False,
        needs_mobile_lift=False,
        required_loaders=2,
        estimated_payload_kg=payload,
        estimated_volume_m3=volume,
        comment=None,
        created_at=now,
        updated_at=now,
    )


async def exercise_offer_distribution() -> None:
    engine = create_async_engine(DATABASE_URL)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)

    async with session_maker() as session:
        carrier_repo = CarrierRepository(session)
        job_repo = JobRepository(session)

        carriers = []
        for idx in range(3):
            carrier = await carrier_repo.create_carrier(
                CarrierCompany(
                    company_name=f"Carrier {idx}",
                    contact_name=None,
                    phone=None,
                    telegram_user_id=4000 + idx,
                    status=CarrierStatus.ACTIVE,
                    paid_until=None,
                    assembly_required=True,
                    packing_required=True,
                    operating_regions="Lisboa",
                    profile_completed_at=now,
                    current_profile_step=None,
                    internal_note=None,
                    created_at=now,
                    updated_at=now,
                )
            )
            carriers.append(carrier)

            await carrier_repo.create_vehicle(
                CarrierVehicle(
                    carrier_id=carrier.id,
                    vehicle_type="large_van",
                    payload_kg=1000 + idx * 500,
                    volume_m3=12.0 + idx,
                    has_tail_lift=True,
                    has_crane=False,
                    has_mobile_lift=False,
                    mobile_lift_max_floor=None,
                    mobile_lift_max_weight_kg=None,
                    crane_max_weight_kg=None,
                    crane_reach_meters=None,
                    max_loaders=2 + idx,
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
            )

        distribution = OfferDistributionService(
            matching_service=JobMatchingService(
                CarrierSearchService(carrier_repo)
            ),
            offer_service=JobOfferService(job_repo),
            job_repository=job_repo,
        )

        offered_job = await job_repo.create_job(
            build_job(now, payload=1000, volume=10.0)
        )

        offers = await distribution.create_offers_for_job(
            offered_job,
            limit=2,
            expires_in_minutes=30,
        )

        loaded_offered_job = await job_repo.get_job_by_id(offered_job.id)
        stored = await job_repo.list_offers_by_job(offered_job.id)

        if len(offers) != 2:
            raise SystemExit(f"expected 2 offers, got {len(offers)}")

        if len(stored) != 2:
            raise SystemExit(f"expected 2 stored offers, got {len(stored)}")

        if loaded_offered_job.status != JobStatus.OFFERED:
            raise SystemExit(f"expected offered status, got {loaded_offered_job.status}")

        unmatched_job = await job_repo.create_job(
            build_job(now, payload=999999, volume=999999.0)
        )

        unmatched_offers = await distribution.create_offers_for_job(
            unmatched_job,
            limit=2,
            expires_in_minutes=30,
        )

        loaded_unmatched_job = await job_repo.get_job_by_id(unmatched_job.id)

        if unmatched_offers:
            raise SystemExit(f"expected no offers, got {len(unmatched_offers)}")

        if loaded_unmatched_job.status != JobStatus.UNMATCHED:
            raise SystemExit(f"expected unmatched status, got {loaded_unmatched_job.status}")

        await session.commit()

    await engine.dispose()


def main() -> None:
    os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
    os.environ["DATABASE_URL"] = DATABASE_URL
    os.environ["ENVIRONMENT"] = "offer-distribution-smoke"
    os.environ["LOG_LEVEL"] = "INFO"

    reset_db()
    run([".venv/bin/alembic", "upgrade", "head"])
    asyncio.run(exercise_offer_distribution())
    shutil.rmtree(DATA_DIR)

    print("OFFER_DISTRIBUTION_SMOKE_OK")


if __name__ == "__main__":
    main()
