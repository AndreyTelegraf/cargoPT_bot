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

    async def add_address(self, address: JobAddress) -> JobAddress:
        self.session.add(address)
        await self.session.flush()
        return address

    async def add_item(self, item: JobItem) -> JobItem:
        self.session.add(item)
        await self.session.flush()
        return item

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

    async def update_job_status(
        self,
        job_id: int,
        status: str,
        updated_at,
    ) -> Job:
        job = await self.get_job_by_id(job_id)

        if job is None:
            raise ValueError("job not found")

        job.status = status
        job.updated_at = updated_at

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
