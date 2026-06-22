from datetime import UTC
from datetime import datetime
from datetime import timedelta

from app.domain.job_offer_status import JobOfferStatus
from app.models.carrier import CarrierVehicle
from app.models.job import JobOffer
from app.repositories.job import JobRepository


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
