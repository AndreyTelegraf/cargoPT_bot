from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.job import JobAddress
from app.models.job import JobItem
from app.models.job import JobMedia
from app.models.job import JobOffer


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_job(self, job: Job) -> Job:
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_job_by_id(self, job_id: int) -> Job | None:
        stmt = select(Job).where(Job.id == job_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_recent_jobs(self, limit: int = 20) -> list[Job]:
        stmt = select(Job).order_by(Job.id.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_address(self, address: JobAddress) -> JobAddress:
        self.session.add(address)
        await self.session.flush()
        return address

    async def list_addresses_by_job(
        self,
        job_id: int,
    ) -> list[JobAddress]:
        stmt = (
            select(JobAddress)
            .where(JobAddress.job_id == job_id)
            .order_by(JobAddress.id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_item(self, item: JobItem) -> JobItem:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_items_by_job(
        self,
        job_id: int,
    ) -> list[JobItem]:
        stmt = (
            select(JobItem)
            .where(JobItem.job_id == job_id)
            .order_by(JobItem.id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_offer(self, offer: JobOffer) -> JobOffer:
        self.session.add(offer)
        await self.session.flush()
        return offer

    async def list_offers_by_job(
        self,
        job_id: int,
    ) -> list[JobOffer]:
        stmt = (
            select(JobOffer)
            .where(JobOffer.job_id == job_id)
            .order_by(JobOffer.id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_offer_by_id(
        self,
        offer_id: int,
    ) -> JobOffer | None:
        stmt = select(JobOffer).where(JobOffer.id == offer_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_offer_status(
        self,
        offer_id: int,
        status: str,
        responded_at,
    ) -> JobOffer:
        offer = await self.get_offer_by_id(offer_id)

        if offer is None:
            raise ValueError("offer not found")

        offer.status = status
        offer.responded_at = responded_at
        offer.updated_at = responded_at

        await self.session.flush()

        return offer

    async def decline_pending_offers_by_job_except(
        self,
        job_id: int,
        accepted_offer_id: int,
        responded_at,
    ) -> list[JobOffer]:
        offers = await self.list_offers_by_job(job_id)
        declined: list[JobOffer] = []

        for offer in offers:
            if offer.id == accepted_offer_id:
                continue
            if offer.status != "pending":
                continue

            offer.status = "declined"
            offer.responded_at = responded_at
            offer.updated_at = responded_at
            declined.append(offer)

        await self.session.flush()
        return declined

    async def update_job_status(
        self,
        job_id: int,
        status: str,
        updated_at,
    ) -> Job:
        job = await self.get_job_by_id(job_id)

        if job is None:
            raise ValueError("job not found")

        status_value = getattr(status, "value", status)

        job.status = status_value
        job.updated_at = updated_at

        if status_value == "assigned" and job.assigned_at is None:
            job.assigned_at = updated_at
        elif status_value == "in_progress" and job.started_at is None:
            job.started_at = updated_at
        elif status_value == "completed" and job.completed_at is None:
            job.completed_at = updated_at
        elif status_value == "cancelled" and job.cancelled_at is None:
            job.cancelled_at = updated_at

        await self.session.flush()

        return job

    async def update_estimated_payload(
        self,
        job_id: int,
        estimated_payload_kg: int | None,
        updated_at,
    ) -> Job:
        job = await self.get_job_by_id(job_id)

        if job is None:
            raise ValueError("job not found")

        job.estimated_payload_kg = estimated_payload_kg
        job.updated_at = updated_at

        await self.session.flush()

        return job

    async def update_estimated_volume(
        self,
        job_id: int,
        estimated_volume_m3: float | None,
        updated_at,
    ) -> Job:
        job = await self.get_job_by_id(job_id)

        if job is None:
            raise ValueError("job not found")

        job.estimated_volume_m3 = estimated_volume_m3
        job.updated_at = updated_at

        await self.session.flush()

        return job

    async def update_required_loaders(
        self,
        job_id: int,
        required_loaders: int | None,
        updated_at,
    ) -> Job:
        job = await self.get_job_by_id(job_id)

        if job is None:
            raise ValueError("job not found")

        job.required_loaders = required_loaders
        job.updated_at = updated_at

        await self.session.flush()

        return job

    async def update_needs_tail_lift(
        self,
        job_id: int,
        needs_tail_lift: bool,
        updated_at,
    ) -> Job:
        job = await self.get_job_by_id(job_id)

        if job is None:
            raise ValueError("job not found")

        job.needs_tail_lift = needs_tail_lift
        job.updated_at = updated_at

        await self.session.flush()

        return job

    async def update_needs_crane(
        self,
        job_id: int,
        needs_crane: bool,
        updated_at,
    ) -> Job:
        job = await self.get_job_by_id(job_id)

        if job is None:
            raise ValueError("job not found")

        job.needs_crane = needs_crane
        job.updated_at = updated_at

        await self.session.flush()

        return job

    async def update_needs_mobile_lift(
        self,
        job_id: int,
        needs_mobile_lift: bool,
        updated_at,
    ) -> Job:
        job = await self.get_job_by_id(job_id)

        if job is None:
            raise ValueError("job not found")

        job.needs_mobile_lift = needs_mobile_lift
        job.updated_at = updated_at

        await self.session.flush()

        return job

    async def update_comment_and_status(
        self,
        job_id: int,
        comment: str | None,
        status: str,
        updated_at,
    ) -> Job:
        job = await self.get_job_by_id(job_id)

        if job is None:
            raise ValueError("job not found")

        job.comment = comment
        job.status = status
        job.updated_at = updated_at

        await self.session.flush()

        return job

    async def add_media(self, media: JobMedia) -> JobMedia:
        self.session.add(media)
        await self.session.flush()
        return media

    async def list_media_by_job(
        self,
        job_id: int,
    ) -> list[JobMedia]:
        stmt = (
            select(JobMedia)
            .where(JobMedia.job_id == job_id)
            .order_by(JobMedia.id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


    async def update_client_phone(
        self,
        job_id: int,
        client_phone: str | None,
        updated_at,
    ) -> Job:
        job = await self.get_job_by_id(job_id)

        if job is None:
            raise ValueError("job not found")

        job.client_phone = client_phone
        job.updated_at = updated_at

        await self.session.flush()

        return job

    async def update_client_whatsapp(
        self,
        job_id: int,
        client_whatsapp: str | None,
        updated_at,
    ) -> Job:
        job = await self.get_job_by_id(job_id)

        if job is None:
            raise ValueError("job not found")

        job.client_whatsapp = client_whatsapp
        job.updated_at = updated_at

        await self.session.flush()

        return job


    async def update_requested_date(
        self,
        job_id: int,
        requested_date,
        updated_at,
    ) -> Job:
        job = await self.get_job_by_id(job_id)

        if job is None:
            raise ValueError("job not found")

        job.requested_date = requested_date
        job.updated_at = updated_at

        await self.session.flush()

        return job
