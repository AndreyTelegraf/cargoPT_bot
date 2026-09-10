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

from app.domain.carrier_status import CarrierStatus
from app.domain.job_offer_status import JobOfferStatus
from app.domain.job_status import JobStatus
from app.models.carrier import CarrierCompany
from app.models.carrier import CarrierVehicle
from app.models.job import Job
from app.repositories.carrier import CarrierRepository
from app.repositories.job import JobRepository
from app.services.job_offer import JobOfferService
from app.services.job_offer import OfferAlreadyResolvedError
from app.services.job_offer import OfferExpiredError
from app.services.job_lifecycle import cancel_client_job

DATA_DIR = PROJECT_ROOT / ".tmp_job_offer_acceptance_smoke"
DATABASE_URL = "sqlite+aiosqlite:///.tmp_job_offer_acceptance_smoke/cargopt_dev.db"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def reset_db() -> None:
    if DATA_DIR == PROJECT_ROOT / "data":
        raise RuntimeError("smoke must not delete PROJECT_ROOT/data")
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(exist_ok=True)


async def exercise_offer_acceptance() -> None:
    engine = create_async_engine(DATABASE_URL)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)

    async with session_maker() as session:
        carrier_repo = CarrierRepository(session)
        job_repo = JobRepository(session)

        carrier = await carrier_repo.create_carrier(
            CarrierCompany(
                company_name="Accept Carrier",
                contact_name=None,
                phone=None,
                telegram_user_id=5001,
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
                status="matching",
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

        offer = await service.create_offer(
            job_id=job.id,
            vehicle=vehicle,
            expires_in_minutes=30,
        )

        accepted = await service.accept_offer(offer.id)

        await session.commit()

        if accepted.status != JobOfferStatus.ACCEPTED:
            raise SystemExit(f"unexpected status: {accepted.status}")

        if accepted.responded_at is None:
            raise SystemExit("responded_at missing")

        expired_offer = await service.create_offer(
            job_id=job.id,
            vehicle=vehicle,
            expires_in_minutes=-1,
        )
        try:
            await service.accept_offer_without_assignment(expired_offer.id)
        except OfferExpiredError:
            pass
        else:
            raise SystemExit("expired pending offer was accepted")

        if expired_offer.status != JobOfferStatus.PENDING:
            raise SystemExit(
                f"expired offer status changed unexpectedly: {expired_offer.status}"
            )
        if expired_offer.responded_at is not None:
            raise SystemExit("expired offer received a response timestamp")

        naive_expiry_offer = await service.create_offer(
            job_id=job.id,
            vehicle=vehicle,
            expires_in_minutes=30,
        )
        naive_expiry_offer.expires_at = datetime.now(UTC).replace(
            tzinfo=None
        ) - timedelta(minutes=1)
        try:
            await service.accept_offer_without_assignment(naive_expiry_offer.id)
        except OfferExpiredError:
            pass
        else:
            raise SystemExit("expired offer with naive SQLite timestamp was accepted")

        cancel_target = await job_repo.create_job(
            Job(
                client_telegram_user_id=9002,
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
        accepted_before_cancel = await service.create_offer(
            job_id=cancel_target.id,
            vehicle=vehicle,
            expires_in_minutes=30,
        )
        await service.accept_offer_without_assignment(
            accepted_before_cancel.id
        )
        pending_before_cancel = await service.create_offer(
            job_id=cancel_target.id,
            vehicle=vehicle,
            expires_in_minutes=30,
        )

        cancelled_job, cancelled_from = await cancel_client_job(
            job_repo,
            job_id=cancel_target.id,
        )
        await session.commit()

        if cancelled_job.status != JobStatus.CANCELLED:
            raise SystemExit("client cancellation did not cancel the job")
        if cancelled_from != JobStatus.OFFERED:
            raise SystemExit(
                f"unexpected client cancellation source: {cancelled_from}"
            )
        cancelled_offers = await job_repo.list_offers_by_job(
            cancel_target.id
        )
        if [str(item.status) for item in cancelled_offers] != [
            "cancelled",
            "cancelled",
        ]:
            raise SystemExit(
                "client cancellation left an offer open: "
                f"{[str(item.status) for item in cancelled_offers]}"
            )
        try:
            await service.accept_offer_without_assignment(
                pending_before_cancel.id
            )
        except OfferAlreadyResolvedError:
            pass
        else:
            raise SystemExit("offer was accepted after client cancellation")

    await engine.dispose()


def main() -> None:
    os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
    os.environ["DATABASE_URL"] = DATABASE_URL
    os.environ["ENVIRONMENT"] = "job-offer-acceptance-smoke"
    os.environ["LOG_LEVEL"] = "INFO"

    reset_db()
    run([".venv/bin/alembic", "upgrade", "head"])
    asyncio.run(exercise_offer_acceptance())
    shutil.rmtree(DATA_DIR)

    print("JOB_OFFER_ACCEPTANCE_SMOKE_OK")


if __name__ == "__main__":
    main()

source = Path("app/services/job_offer.py").read_text(encoding="utf-8")
assert "accept_offer_without_assignment" in source
assert "decline_pending_offers_by_job_except" not in source[source.index("async def accept_offer_without_assignment"):source.index("async def accept_offer_and_assign_job")]
assert "status=JobStatus.OFFERED" in source[source.index("async def accept_offer_without_assignment"):source.index("async def accept_offer_and_assign_job")]
assert "_ensure_offer_accepts_response" in source
