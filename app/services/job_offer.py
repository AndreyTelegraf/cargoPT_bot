from datetime import UTC
from datetime import datetime
from datetime import timedelta

from app.domain.job_offer_status import JobOfferStatus
from app.domain.job_status import JobStatus
from app.models.carrier import CarrierVehicle
from app.models.job import JobOffer
from app.repositories.job import JobRepository


class OfferAlreadyResolvedError(ValueError):
    pass


class JobAlreadyAssignedError(ValueError):
    pass


class JobOfferService:
    def __init__(self, repository: JobRepository) -> None:
        self.repository = repository

    async def create_offer(
        self,
        *,
        job_id: int,
        vehicle: CarrierVehicle,
        expires_in_minutes: int = 60,
    ) -> JobOffer:
        now = datetime.now(UTC)

        offer = JobOffer(
            job_id=job_id,
            carrier_id=vehicle.carrier_id,
            vehicle_id=vehicle.id,
            status=JobOfferStatus.PENDING,
            offered_at=now,
            responded_at=None,
            expires_at=now + timedelta(minutes=expires_in_minutes),
            carrier_note=None,
            price_cents=None,
            created_at=now,
            updated_at=now,
        )

        return await self.repository.create_offer(offer)

    async def accept_offer(
        self,
        offer_id: int,
    ) -> JobOffer:
        now = datetime.now(UTC)
        return await self.repository.update_offer_status(
            offer_id=offer_id,
            status=JobOfferStatus.ACCEPTED,
            responded_at=now,
        )

    async def decline_offer(
        self,
        offer_id: int,
    ) -> JobOffer:
        now = datetime.now(UTC)
        return await self.repository.update_offer_status(
            offer_id=offer_id,
            status=JobOfferStatus.DECLINED,
            responded_at=now,
        )

    async def accept_offer_and_assign_job(
        self,
        offer_id: int,
    ) -> JobOffer:
        now = datetime.now(UTC)

        offer = await self.repository.get_offer_by_id(offer_id)

        if offer is None:
            raise ValueError("offer not found")

        if offer.status != JobOfferStatus.PENDING:
            raise OfferAlreadyResolvedError("offer already resolved")

        job = await self.repository.get_job_by_id(offer.job_id)

        if job is None:
            raise ValueError("job not found")

        if job.status in {
            JobStatus.ASSIGNED_PENDING_CONFIRMATION,
            JobStatus.ASSIGNED,
        }:
            raise JobAlreadyAssignedError("job already assigned")

        offer.status = JobOfferStatus.ACCEPTED
        offer.responded_at = now
        offer.updated_at = now

        await self.repository.update_job_status(
            job_id=offer.job_id,
            status=JobStatus.ASSIGNED_PENDING_CONFIRMATION,
            updated_at=now,
        )

        await self.repository.decline_pending_offers_by_job_except(
            job_id=offer.job_id,
            accepted_offer_id=offer.id,
            responded_at=now,
        )

        return offer
