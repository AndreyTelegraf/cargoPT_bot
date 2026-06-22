from datetime import UTC
from datetime import datetime

from app.domain.job_status import JobStatus
from app.models.job import Job
from app.models.job import JobAddress
from app.models.job import JobItem
from app.models.job import JobMedia
from app.repositories.job import JobRepository
from app.services.location_normalization import build_google_maps_coordinate_url
from app.services.location_normalization import normalize_text_location


class JobService:
    def __init__(self, repository: JobRepository) -> None:
        self.repository = repository

    async def create_draft_job(
        self,
        *,
        client_telegram_user_id: int,
        client_telegram_username: str | None = None,
        comment: str | None = None,
    ) -> Job:
        now = datetime.now(UTC)

        job = Job(
            client_telegram_user_id=client_telegram_user_id,
            client_telegram_username=client_telegram_username,
            client_phone=None,
            client_whatsapp=None,
            status=JobStatus.DRAFT,
            requested_date=None,
            needs_assembly=False,
            needs_packing=False,
            needs_tail_lift=False,
            needs_crane=False,
            needs_mobile_lift=False,
            required_loaders=None,
            estimated_payload_kg=None,
            estimated_volume_m3=None,
            comment=comment,
            created_at=now,
            updated_at=now,
        )

        return await self.repository.create_job(job)

    async def add_address(
        self,
        *,
        job_id: int,
        kind: str,
        raw_text: str,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> JobAddress:
        if latitude is not None and longitude is not None:
            normalized_text = raw_text.strip() or f"{latitude}, {longitude}"
            map_url = build_google_maps_coordinate_url(latitude, longitude)
        else:
            normalized_text, map_url = normalize_text_location(raw_text)

        address = JobAddress(
            job_id=job_id,
            kind=kind,
            raw_text=normalized_text,
            city=None,
            postal_code=None,
            floor=None,
            has_elevator=None,
            latitude=latitude,
            longitude=longitude,
            map_url=map_url,
            created_at=datetime.now(UTC),
        )

        return await self.repository.add_address(address)

    async def add_item(
        self,
        *,
        job_id: int,
        description: str,
        quantity: int | None = None,
    ) -> JobItem:
        item = JobItem(
            job_id=job_id,
            description=description,
            quantity=quantity,
            estimated_weight_kg=None,
            estimated_volume_m3=None,
            created_at=datetime.now(UTC),
        )

        return await self.repository.add_item(item)

    async def update_estimated_payload(
        self,
        *,
        job_id: int,
        estimated_payload_kg: int | None,
    ) -> Job:
        return await self.repository.update_estimated_payload(
            job_id=job_id,
            estimated_payload_kg=estimated_payload_kg,
            updated_at=datetime.now(UTC),
        )

    async def update_estimated_volume(
        self,
        *,
        job_id: int,
        estimated_volume_m3: float | None,
    ) -> Job:
        return await self.repository.update_estimated_volume(
            job_id=job_id,
            estimated_volume_m3=estimated_volume_m3,
            updated_at=datetime.now(UTC),
        )

    async def update_required_loaders(
        self,
        *,
        job_id: int,
        required_loaders: int | None,
    ) -> Job:
        return await self.repository.update_required_loaders(
            job_id=job_id,
            required_loaders=required_loaders,
            updated_at=datetime.now(UTC),
        )

    async def update_needs_tail_lift(
        self,
        *,
        job_id: int,
        needs_tail_lift: bool,
    ) -> Job:
        return await self.repository.update_needs_tail_lift(
            job_id=job_id,
            needs_tail_lift=needs_tail_lift,
            updated_at=datetime.now(UTC),
        )

    async def update_needs_crane(
        self,
        *,
        job_id: int,
        needs_crane: bool,
    ) -> Job:
        return await self.repository.update_needs_crane(
            job_id=job_id,
            needs_crane=needs_crane,
            updated_at=datetime.now(UTC),
        )

    async def update_needs_mobile_lift(
        self,
        *,
        job_id: int,
        needs_mobile_lift: bool,
    ) -> Job:
        return await self.repository.update_needs_mobile_lift(
            job_id=job_id,
            needs_mobile_lift=needs_mobile_lift,
            updated_at=datetime.now(UTC),
        )

    async def finalize_for_matching(
        self,
        *,
        job_id: int,
        comment: str | None,
    ) -> Job:
        return await self.repository.update_comment_and_status(
            job_id=job_id,
            comment=comment,
            status=JobStatus.READY_FOR_MATCHING,
            updated_at=datetime.now(UTC),
        )

    async def add_media(
        self,
        *,
        job_id: int,
        media_type: str,
        telegram_file_id: str,
        caption: str | None = None,
    ) -> JobMedia:
        media = JobMedia(
            job_id=job_id,
            media_type=media_type,
            telegram_file_id=telegram_file_id,
            caption=caption,
            created_at=datetime.now(UTC),
        )

        return await self.repository.add_media(media)


    async def update_client_phone(
        self,
        *,
        job_id: int,
        client_phone: str | None,
    ) -> Job:
        return await self.repository.update_client_phone(
            job_id=job_id,
            client_phone=client_phone,
            updated_at=datetime.now(UTC),
        )

    async def update_client_whatsapp(
        self,
        *,
        job_id: int,
        client_whatsapp: str | None,
    ) -> Job:
        return await self.repository.update_client_whatsapp(
            job_id=job_id,
            client_whatsapp=client_whatsapp,
            updated_at=datetime.now(UTC),
        )


    async def update_requested_date(
        self,
        *,
        job_id: int,
        requested_date,
    ) -> Job:
        return await self.repository.update_requested_date(
            job_id=job_id,
            requested_date=requested_date,
            updated_at=datetime.now(UTC),
        )
