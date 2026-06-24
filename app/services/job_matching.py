from app.models.carrier import CarrierVehicle
from app.models.job import Job
from app.services.carrier_search import CarrierSearchService


class JobMatchingService:
    def __init__(self, carrier_search: CarrierSearchService) -> None:
        self.carrier_search = carrier_search

    async def find_matching_vehicles_for_job(
        self,
        job: Job,
    ) -> list[CarrierVehicle]:
        return await self.carrier_search.find_matching_vehicles(
            min_payload_kg=job.estimated_payload_kg,
            min_volume_m3=job.estimated_volume_m3,
            min_loaders=job.required_loaders,
            needs_tail_lift=job.needs_tail_lift,
            needs_crane=job.needs_crane,
            needs_mobile_lift=job.needs_mobile_lift,
            needs_assembly=job.needs_assembly,
            needs_packing=job.needs_packing,
        )
