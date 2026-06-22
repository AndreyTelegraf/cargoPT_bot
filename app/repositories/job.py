from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.job import JobAddress
from app.models.job import JobItem


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
