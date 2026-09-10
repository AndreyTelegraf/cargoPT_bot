import asyncio
import os
import shutil
import subprocess
import sys
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / ".tmp_request_submission_transaction_boundary_smoke"
DATABASE_URL = (
    "sqlite+aiosqlite:///"
    ".tmp_request_submission_transaction_boundary_smoke/cargopt_dev.db"
)

sys.path.insert(0, str(PROJECT_ROOT))
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = DATABASE_URL
os.environ["ENVIRONMENT"] = "request-submission-transaction-boundary-smoke"

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from app.domain.carrier_status import CarrierStatus
from app.domain.job_status import JobStatus
from app.models.carrier import CarrierCompany
from app.models.carrier import CarrierVehicle
from app.models.job import Job
from app.models.job import JobOffer
from app.repositories.carrier import CarrierRepository
from app.repositories.job import JobRepository
from app.services import job_escalation
from app.services.request_intake import RequestIntakeAddress
from app.services.request_intake import RequestIntakeInput
from app.services.request_intake import RequestIntakeItem
from app.services.request_intake import RequestIntakeService


class FailingBot:
    def __init__(self, fail_on_call: int) -> None:
        self.fail_on_call = fail_on_call
        self.calls = []

    async def send_message(self, *, chat_id, text, **kwargs):
        self.calls.append(chat_id)
        if len(self.calls) == self.fail_on_call:
            raise RuntimeError(
                f"simulated Telegram failure on call {self.fail_on_call}"
            )
        return SimpleNamespace(
            chat=SimpleNamespace(id=chat_id),
            message_id=9000 + len(self.calls),
        )


def reset_db() -> None:
    if DATA_DIR == PROJECT_ROOT / "data":
        raise RuntimeError("smoke must not delete PROJECT_ROOT/data")
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir()


def make_request(
    *,
    sequence: int,
    now: datetime,
    pickup: tuple[str, float, float] = ("Lisboa", 38.7223, -9.1393),
    dropoff: tuple[str, float, float] = ("Porto", 41.1579, -8.6291),
    days_until_move: int = 30,
) -> RequestIntakeInput:
    return RequestIntakeInput(
        source_locale="pt",
        customer_name=f"C01 Client {sequence}",
        customer_email=f"c01-{sequence}@example.test",
        preferred_contact="email",
        client_phone=None,
        client_whatsapp=None,
        utm_source=None,
        utm_medium=None,
        utm_campaign=None,
        utm_content=None,
        landing_version=None,
        requested_date=now + timedelta(days=days_until_move),
        addresses=(
            RequestIntakeAddress(
                kind="pickup",
                raw_text=pickup[0],
                normalized_address=pickup[0],
                latitude=pickup[1],
                longitude=pickup[2],
                country_code="pt",
            ),
            RequestIntakeAddress(
                kind="dropoff",
                raw_text=dropoff[0],
                normalized_address=dropoff[0],
                latitude=dropoff[1],
                longitude=dropoff[2],
                country_code="pt",
            ),
        ),
        items=(RequestIntakeItem(description="Boxes", quantity=5),),
        estimated_payload_kg=500,
        estimated_volume_m3=5.0,
        comment="C01 transaction boundary smoke",
    )


async def create_three_carriers(session, now: datetime) -> None:
    repository = CarrierRepository(session)
    for index in range(3):
        carrier = await repository.create_carrier(
            CarrierCompany(
                company_name=f"C01 Carrier {index + 1}",
                contact_name=None,
                phone=None,
                telegram_user_id=5100 + index,
                status=CarrierStatus.ACTIVE,
                paid_until=now + timedelta(days=30),
                assembly_required=False,
                packing_required=False,
                operating_regions="Lisboa,Porto",
                profile_completed_at=now,
                current_profile_step=None,
                internal_note=None,
                created_at=now,
                updated_at=now,
            )
        )
        await repository.create_vehicle(
            CarrierVehicle(
                carrier_id=carrier.id,
                vehicle_type="large_van",
                payload_kg=1500,
                volume_m3=15.0,
                has_tail_lift=False,
                has_crane=False,
                has_mobile_lift=False,
                mobile_lift_max_floor=None,
                mobile_lift_max_weight_kg=None,
                crane_max_weight_kg=None,
                crane_reach_meters=None,
                max_loaders=2,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        )
    await session.commit()


async def counts(session_maker) -> tuple[int, int]:
    async with session_maker() as session:
        jobs = int((await session.execute(select(func.count(Job.id)))).scalar_one())
        offers = int(
            (await session.execute(select(func.count(JobOffer.id)))).scalar_one()
        )
        return jobs, offers


async def submit_expecting_delivery_failure(
    *,
    session_maker,
    request: RequestIntakeInput,
    fail_on_call: int,
) -> FailingBot:
    async with session_maker() as session:
        bot = FailingBot(fail_on_call)
        service = RequestIntakeService(
            job_repository=JobRepository(session),
            carrier_repository=CarrierRepository(session),
            bot=bot,
        )
        try:
            await service.submit_web_intake(request)
        except RuntimeError as exc:
            if "simulated Telegram failure" not in str(exc):
                raise
            await session.rollback()
        else:
            raise AssertionError("Telegram failure did not propagate")
        return bot


async def exercise() -> None:
    engine = create_async_engine(DATABASE_URL)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)

    async with session_maker() as session:
        await create_three_carriers(session, now)

    for sequence, fail_on_call in enumerate((1, 2, 3), start=1):
        bot = await submit_expecting_delivery_failure(
            session_maker=session_maker,
            request=make_request(sequence=sequence, now=now),
            fail_on_call=fail_on_call,
        )
        if len(bot.calls) != fail_on_call:
            raise AssertionError(f"unexpected Telegram calls: {bot.calls}")
        actual = await counts(session_maker)
        expected = (sequence, sequence * 3)
        if actual != expected:
            raise AssertionError(
                f"delivery failure lost durable data: expected={expected} actual={actual}"
            )

    original_recipients = job_escalation.JOB_CONTROL_TELEGRAM_USER_IDS
    job_escalation.JOB_CONTROL_TELEGRAM_USER_IDS = (99001,)
    try:
        manual_bot = await submit_expecting_delivery_failure(
            session_maker=session_maker,
            request=make_request(
                sequence=4,
                now=now,
                pickup=("Faro", 37.0194, -7.9304),
                dropoff=("Faro", 37.0194, -7.9304),
            ),
            fail_on_call=1,
        )
        if manual_bot.calls != [99001]:
            raise AssertionError(f"manual review was not attempted: {manual_bot.calls}")
        actual = await counts(session_maker)
        if actual != (4, 9):
            raise AssertionError(f"manual review failure lost job: {actual}")

        async with session_maker() as session:
            latest_job = (
                await session.execute(select(Job).order_by(Job.id.desc()).limit(1))
            ).scalar_one()
            if latest_job.status != JobStatus.MANUAL_REVIEW_REQUIRED:
                raise AssertionError(
                    f"manual review status was not durable: {latest_job.status}"
                )
    finally:
        job_escalation.JOB_CONTROL_TELEGRAM_USER_IDS = original_recipients

    await engine.dispose()


def main() -> None:
    reset_db()
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=PROJECT_ROOT,
        check=True,
    )
    asyncio.run(exercise())
    shutil.rmtree(DATA_DIR)
    print("REQUEST_SUBMISSION_TRANSACTION_BOUNDARY_SMOKE_OK")


if __name__ == "__main__":
    main()
