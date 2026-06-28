from dataclasses import dataclass
from datetime import UTC
from datetime import datetime

from app.domain.job_status import JobStatus
from app.models.job import Job
from app.repositories.carrier import CarrierRepository
from app.repositories.job import JobRepository
from app.services.request_submission import RequestSubmissionResult
from app.services.request_submission import RequestSubmissionService
from app.services.request_update import RequestUpdateService


@dataclass(frozen=True)
class WebIntakeAddress:
    kind: str
    raw_text: str
    floor: int | None = None
    has_elevator: bool | None = None


@dataclass(frozen=True)
class WebIntakeItem:
    description: str
    quantity: int | None = None


@dataclass(frozen=True)
class WebIntakeRequest:
    source_locale: str | None
    customer_name: str | None
    customer_email: str | None
    preferred_contact: str | None
    client_phone: str | None
    client_whatsapp: str | None
    utm_source: str | None
    utm_campaign: str | None
    landing_version: str | None
    requested_date: datetime | None
    addresses: tuple[WebIntakeAddress, ...]
    items: tuple[WebIntakeItem, ...]
    needs_assembly: bool = False
    needs_packing: bool = False
    needs_tail_lift: bool = False
    needs_crane: bool = False
    needs_mobile_lift: bool = False
    required_loaders: int | None = None
    estimated_payload_kg: int | None = None
    estimated_volume_m3: float | None = None
    comment: str | None = None


class WebIntakeService:
    def __init__(
        self,
        *,
        job_repository: JobRepository,
        carrier_repository: CarrierRepository,
        bot,
    ) -> None:
        self.job_repository = job_repository
        self.carrier_repository = carrier_repository
        self.bot = bot

    async def submit_web_request(self, request: WebIntakeRequest) -> RequestSubmissionResult:
        now = datetime.now(UTC)
        job = Job(
            client_telegram_user_id=None,
            client_telegram_username=None,
            source="web_form",
            source_locale=request.source_locale,
            customer_name=request.customer_name,
            customer_email=request.customer_email,
            preferred_contact=request.preferred_contact,
            client_phone=request.client_phone,
            client_whatsapp=request.client_whatsapp,
            utm_source=request.utm_source,
            utm_campaign=request.utm_campaign,
            landing_version=request.landing_version,
            status=JobStatus.DRAFT,
            requested_date=request.requested_date,
            assigned_at=None,
            started_at=None,
            completed_at=None,
            cancelled_at=None,
            client_confirmation_status=None,
            carrier_confirmation_status=None,
            needs_assembly=request.needs_assembly,
            needs_packing=request.needs_packing,
            needs_tail_lift=request.needs_tail_lift,
            needs_crane=request.needs_crane,
            needs_mobile_lift=request.needs_mobile_lift,
            required_loaders=request.required_loaders,
            estimated_payload_kg=request.estimated_payload_kg,
            estimated_volume_m3=request.estimated_volume_m3,
            comment=None,
            created_at=now,
            updated_at=now,
        )
        job = await self.job_repository.create_job(job)

        update_service = RequestUpdateService(job_repository=self.job_repository)
        for address_payload in request.addresses:
            address = await update_service.add_address(
                job_id=job.id,
                kind=address_payload.kind,
                raw_text=address_payload.raw_text,
            )
            if address_payload.floor is not None or address_payload.has_elevator is not None:
                await update_service.update_address_details(
                    address_id=address.id,
                    floor=address_payload.floor,
                    has_elevator=address_payload.has_elevator,
                )

        for item_payload in request.items:
            await update_service.add_item(
                job_id=job.id,
                description=item_payload.description,
                quantity=item_payload.quantity,
            )

        submission_service = RequestSubmissionService(
            job_repository=self.job_repository,
            carrier_repository=self.carrier_repository,
            bot=self.bot,
        )
        return await submission_service.submit_existing_job(
            job_id=job.id,
            comment=request.comment,
            enforce_telegram_client_limits=False,
        )
