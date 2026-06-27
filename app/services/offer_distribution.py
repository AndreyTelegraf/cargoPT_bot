from app.domain.job_status import JobStatus
from app.models.job import Job
from app.models.job import JobOffer
from app.repositories.job import JobRepository
from app.services.job_matching import JobMatchingService
from app.services.job_offer import JobOfferService


class OfferDistributionService:
    def __init__(
        self,
        *,
        matching_service: JobMatchingService,
        offer_service: JobOfferService,
        job_repository: JobRepository,
    ) -> None:
        self.matching_service = matching_service
        self.offer_service = offer_service
        self.job_repository = job_repository

    async def create_offers_for_job(
        self,
        job: Job,
        *,
        limit: int | None = None,
        expires_in_minutes: int = 60,
    ) -> list[JobOffer]:
        await self.job_repository.update_job_status(
            job_id=job.id,
            status=JobStatus.MATCHING,
            updated_at=job.updated_at,
        )

        existing_carrier_ids = await self.job_repository.list_offer_carrier_ids_by_job(job.id)
        addresses = await self.job_repository.list_addresses_by_job(job.id)
        vehicles = await self.matching_service.find_matching_vehicles_for_job(
            job,
            addresses=addresses,
        )
        if not vehicles:
            vehicles = await self.matching_service.carrier_search.find_matching_vehicles()

        selected = [
            vehicle for vehicle in vehicles
            if vehicle.carrier_id not in existing_carrier_ids
        ]

        if limit is not None:
            selected = selected[:limit]

        offers = []

        for vehicle in selected:
            offer = await self.offer_service.create_offer(
                job_id=job.id,
                vehicle=vehicle,
                expires_in_minutes=expires_in_minutes,
            )
            offers.append(offer)

        target_status = JobStatus.OFFERED if offers else JobStatus.NO_CARRIERS_FOUND

        await self.job_repository.update_job_status(
            job_id=job.id,
            status=target_status,
            updated_at=job.updated_at,
        )

        return offers
