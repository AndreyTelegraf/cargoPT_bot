from dataclasses import dataclass

from app.models.job import Job
from app.repositories.job import JobRepository
from app.services.job import JobService


class ClientBannedError(ValueError):
    pass


@dataclass(frozen=True)
class RequestDraftResult:
    job: Job
    reused_existing_draft: bool


def draft_has_no_progress(job, addresses, items) -> bool:
    return (
        not addresses
        and not items
        and job.requested_date is None
        and job.estimated_payload_kg is None
        and job.estimated_volume_m3 is None
        and job.required_loaders is None
        and job.client_phone is None
        and job.client_whatsapp is None
        and job.comment is None
    )


class RequestDraftService:
    def __init__(self, *, job_repository: JobRepository) -> None:
        self.job_repository = job_repository

    async def create_or_reuse_telegram_draft(
        self,
        *,
        client_telegram_user_id: int,
        client_telegram_username: str | None,
    ) -> RequestDraftResult:
        ban = await self.job_repository.get_active_client_ban(client_telegram_user_id)
        if ban is not None:
            raise ClientBannedError("client_banned")

        latest_draft = await self.job_repository.get_latest_draft_job_by_client_id(
            client_telegram_user_id
        )

        if latest_draft is not None:
            addresses = await self.job_repository.list_addresses_by_job(latest_draft.id)
            items = await self.job_repository.list_items_by_job(latest_draft.id)
        else:
            addresses = []
            items = []

        if latest_draft is not None and draft_has_no_progress(latest_draft, addresses, items):
            return RequestDraftResult(
                job=latest_draft,
                reused_existing_draft=True,
            )

        service = JobService(self.job_repository)
        job = await service.create_draft_job(
            client_telegram_user_id=client_telegram_user_id,
            client_telegram_username=client_telegram_username,
        )

        return RequestDraftResult(
            job=job,
            reused_existing_draft=False,
        )
