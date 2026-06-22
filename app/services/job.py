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

    async def update_estimated_payload(
        self,
        *,
        job_id: int,
        estimated_payload_kg: int | None,
    ) -> Job:
        return await self.repository.update_estimated_payload(
            job_id=job_id,
            estimated_payload_kg=estimated_payload_kg,
            updated_at=datetime.now(UTC),
        )

    async def update_estimated_volume(
        self,
        *,
        job_id: int,
        estimated_volume_m3: float | None,
    ) -> Job:
        return await self.repository.update_estimated_volume(
            job_id=job_id,
            estimated_volume_m3=estimated_volume_m3,
            updated_at=datetime.now(UTC),
        )

    async def update_required_loaders(
        self,
        *,
        job_id: int,
        required_loaders: int | None,
    ) -> Job:
        return await self.repository.update_required_loaders(
            job_id=job_id,
            required_loaders=required_loaders,
            updated_at=datetime.now(UTC),
        )

    async def update_needs_tail_lift(
        self,
        *,
        job_id: int,
        needs_tail_lift: bool,
    ) -> Job:
        return await self.repository.update_needs_tail_lift(
            job_id=job_id,
            needs_tail_lift=needs_tail_lift,
            updated_at=datetime.now(UTC),
        )

    async def update_needs_crane(
        self,
        *,
        job_id: int,
        needs_crane: bool,
    ) -> Job:
        return await self.repository.update_needs_crane(
            job_id=job_id,
            needs_crane=needs_crane,
            updated_at=datetime.now(UTC),
        )

    async def update_needs_mobile_lift(
        self,
        *,
        job_id: int,
        needs_mobile_lift: bool,
    ) -> Job:
        return await self.repository.update_needs_mobile_lift(
            job_id=job_id,
            needs_mobile_lift=needs_mobile_lift,
            updated_at=datetime.now(UTC),
        )
