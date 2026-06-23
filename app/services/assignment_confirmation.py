from datetime import UTC
from datetime import datetime

from app.domain.job_status import JobStatus
from app.models.job import Job
from app.repositories.carrier import CarrierRepository
from app.services.job import InvalidJobStatusTransitionError
from app.services.job import JobService
from app.services.job import _transition_job_status


ASSIGNMENT_CONFIRMATION_CONFIRMED = "confirmed"
ASSIGNMENT_CONFIRMATION_FAILED = "failed"


class InvalidAssignmentConfirmationActorError(ValueError):
    pass


class InvalidAssignmentConfirmationStatusError(ValueError):
    pass


async def resolve_assignment_actor(
    *,
    telegram_user_id: int,
    job,
    accepted_offer,
    carrier_repository: CarrierRepository,
) -> str | None:
    if job.client_telegram_user_id == telegram_user_id:
        return "client"

    carrier = await carrier_repository.get_carrier_by_telegram_user_id(telegram_user_id)
    if carrier is None or accepted_offer is None:
        return None

    if accepted_offer.carrier_id == carrier.id:
        return "carrier"

    return None


async def evaluate_assignment_confirmation(service: JobService, *, job_id: int) -> Job:
    job = await service.repository.get_job_by_id(job_id)

    if job is None:
        raise ValueError("job not found")

    current_status = JobStatus(job.status)
    if current_status != JobStatus.ASSIGNED_PENDING_CONFIRMATION:
        raise InvalidJobStatusTransitionError(
            f"cannot evaluate assignment confirmation for job {job_id} from {current_status}"
        )

    votes = {
        job.client_confirmation_status,
        job.carrier_confirmation_status,
    }

    if ASSIGNMENT_CONFIRMATION_FAILED in votes:
        await service.repository.clear_assignment_confirmation_statuses(
            job_id=job_id,
            updated_at=datetime.now(UTC),
        )
        return await _transition_job_status(
            service,
            job_id=job_id,
            allowed_from={JobStatus.ASSIGNED_PENDING_CONFIRMATION},
            target_status=JobStatus.READY_FOR_MATCHING,
        )

    if (
        job.client_confirmation_status == ASSIGNMENT_CONFIRMATION_CONFIRMED
        and job.carrier_confirmation_status == ASSIGNMENT_CONFIRMATION_CONFIRMED
    ):
        return await _transition_job_status(
            service,
            job_id=job_id,
            allowed_from={JobStatus.ASSIGNED_PENDING_CONFIRMATION},
            target_status=JobStatus.ASSIGNED,
        )

    return job


async def record_assignment_confirmation(
    service: JobService,
    *,
    job_id: int,
    actor: str,
    status: str,
) -> Job:
    if actor not in {"client", "carrier"}:
        raise InvalidAssignmentConfirmationActorError("invalid assignment confirmation actor")

    if status not in {
        ASSIGNMENT_CONFIRMATION_CONFIRMED,
        ASSIGNMENT_CONFIRMATION_FAILED,
    }:
        raise InvalidAssignmentConfirmationStatusError("invalid assignment confirmation status")

    job = await service.repository.get_job_by_id(job_id)

    if job is None:
        raise ValueError("job not found")

    if JobStatus(job.status) != JobStatus.ASSIGNED_PENDING_CONFIRMATION:
        raise InvalidJobStatusTransitionError(
            f"cannot record assignment confirmation for job {job_id} from {job.status}"
        )

    await service.repository.update_assignment_confirmation_status(
        job_id=job_id,
        actor=actor,
        status=status,
        updated_at=datetime.now(UTC),
    )

    return await evaluate_assignment_confirmation(service, job_id=job_id)
