from datetime import UTC
from datetime import datetime

from app.domain.job_status import JobStatus
from app.models.job import Job
from app.services.job import InvalidJobStatusTransitionError
from app.services.job import JobService
from app.services.job import _transition_job_status


ASSIGNMENT_CONFIRMATION_CONFIRMED = "confirmed"
ASSIGNMENT_CONFIRMATION_FAILED = "failed"


class InvalidAssignmentConfirmationActorError(ValueError):
    pass


class InvalidAssignmentConfirmationStatusError(ValueError):
    pass


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
