from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.job import JobAddress
from app.models.job import JobItem
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
