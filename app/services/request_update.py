from app.models.job import Job
from app.models.job import JobAddress
from app.models.job import JobItem
from app.repositories.job import JobRepository
from app.services.job import JobService


class RequestUpdateService:
    def __init__(self, *, job_repository: JobRepository) -> None:
        self.job_service = JobService(job_repository)

    async def add_address(
        self,
        *,
        job_id: int,
        kind: str,
        raw_text: str,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> JobAddress:
        return await self.job_service.add_address(
            job_id=job_id,
            kind=kind,
            raw_text=raw_text,
            latitude=latitude,
            longitude=longitude,
        )

    async def update_address_details(
        self,
        *,
        address_id: int,
        floor: int | None,
        has_elevator: bool | None,
    ) -> JobAddress:
        return await self.job_service.update_address_details(
            address_id=address_id,
            floor=floor,
            has_elevator=has_elevator,
        )

    async def add_item(
        self,
        *,
        job_id: int,
        description: str,
        quantity: int | None = None,
    ) -> JobItem:
        return await self.job_service.add_item(
            job_id=job_id,
            description=description,
            quantity=quantity,
        )

    async def update_estimated_payload(
        self,
        *,
        job_id: int,
        estimated_payload_kg: int | None,
    ) -> Job:
        return await self.job_service.update_estimated_payload(
            job_id=job_id,
            estimated_payload_kg=estimated_payload_kg,
        )

    async def update_estimated_volume(
        self,
        *,
        job_id: int,
        estimated_volume_m3: float | None,
    ) -> Job:
        return await self.job_service.update_estimated_volume(
            job_id=job_id,
            estimated_volume_m3=estimated_volume_m3,
        )

    async def update_required_loaders(
        self,
        *,
        job_id: int,
        required_loaders: int | None,
    ) -> Job:
        return await self.job_service.update_required_loaders(
            job_id=job_id,
            required_loaders=required_loaders,
        )

    async def update_needs_assembly(
        self,
        *,
        job_id: int,
        needs_assembly: bool,
    ) -> Job:
        return await self.job_service.update_needs_assembly(
            job_id=job_id,
            needs_assembly=needs_assembly,
        )

    async def update_needs_packing(
        self,
        *,
        job_id: int,
        needs_packing: bool,
    ) -> Job:
        return await self.job_service.update_needs_packing(
            job_id=job_id,
            needs_packing=needs_packing,
        )

    async def update_needs_tail_lift(
        self,
        *,
        job_id: int,
        needs_tail_lift: bool,
    ) -> Job:
        return await self.job_service.update_needs_tail_lift(
            job_id=job_id,
            needs_tail_lift=needs_tail_lift,
        )

    async def update_needs_crane(
        self,
        *,
        job_id: int,
        needs_crane: bool,
    ) -> Job:
        return await self.job_service.update_needs_crane(
            job_id=job_id,
            needs_crane=needs_crane,
        )

    async def update_needs_mobile_lift(
        self,
        *,
        job_id: int,
        needs_mobile_lift: bool,
    ) -> Job:
        return await self.job_service.update_needs_mobile_lift(
            job_id=job_id,
            needs_mobile_lift=needs_mobile_lift,
        )

    async def update_requested_date(
        self,
        *,
        job_id: int,
        requested_date,
    ) -> Job:
        return await self.job_service.update_requested_date(
            job_id=job_id,
            requested_date=requested_date,
        )

    async def update_client_phone(
        self,
        *,
        job_id: int,
        client_phone: str | None,
    ) -> Job:
        return await self.job_service.update_client_phone(
            job_id=job_id,
            client_phone=client_phone,
        )

    async def update_client_whatsapp(
        self,
        *,
        job_id: int,
        client_whatsapp: str | None,
    ) -> Job:
        return await self.job_service.update_client_whatsapp(
            job_id=job_id,
            client_whatsapp=client_whatsapp,
        )

    async def add_media(
        self,
        *,
        job_id: int,
        telegram_file_id: str,
        media_type: str,
        caption: str | None = None,
    ):
        return await self.job_service.add_media(
            job_id=job_id,
            telegram_file_id=telegram_file_id,
            media_type=media_type,
            caption=caption,
        )
