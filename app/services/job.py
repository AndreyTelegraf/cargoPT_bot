from datetime import UTC
from datetime import datetime

from app.domain.job_status import JobStatus
from app.models.job import Job
from app.models.job import JobAddress
from app.models.job import JobItem
from app.repositories.job import JobRepository


class JobService:
    def __init__(self, repository: JobRepository) -> None:
        self.repository = repository

    async def create_draft_job(
        self,
        *,
        client_telegram_user_id: int,
        comment: str | None = None,
    ) -> Job:
        now = datetime.now(UTC)

        job = Job(
            client_telegram_user_id=client_telegram_user_id,
            status=JobStatus.DRAFT,
            requested_date=None,
            needs_assembly=False,
            needs_packing=False,
            needs_tail_lift=False,
            needs_crane=False,
            needs_mobile_lift=False,
            required_loaders=None,
            estimated_payload_kg=None,
            estimated_volume_m3=None,
            comment=comment,
            created_at=now,
            updated_at=now,
        )

        return await self.repository.create_job(job)

    async def add_address(
        self,
        *,
        job_id: int,
        kind: str,
        raw_text: str,
    ) -> JobAddress:
        address = JobAddress(
            job_id=job_id,
            kind=kind,
            raw_text=raw_text,
            city=None,
            postal_code=None,
            floor=None,
            has_elevator=None,
            latitude=None,
            longitude=None,
            map_url=None,
            created_at=datetime.now(UTC),
        )

        return await self.repository.add_address(address)

    async def add_item(
        self,
        *,
        job_id: int,
        description: str,
        quantity: int | None = None,
    ) -> JobItem:
        item = JobItem(
            job_id=job_id,
            description=description,
            quantity=quantity,
            estimated_weight_kg=None,
            estimated_volume_m3=None,
            created_at=datetime.now(UTC),
        )

        return await self.repository.add_item(item)
