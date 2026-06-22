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
        limit: int = 5,
        expires_in_minutes: int = 60,
    ) -> list[JobOffer]:
        vehicles = await self.matching_service.find_matching_vehicles_for_job(job)
        selected = vehicles[:limit]

        offers = []

        for vehicle in selected:
            offer = await self.offer_service.create_offer(
                job_id=job.id,
                vehicle=vehicle,
                expires_in_minutes=expires_in_minutes,
            )
            offers.append(offer)

        return offers
