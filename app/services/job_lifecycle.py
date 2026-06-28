from datetime import UTC
from datetime import datetime

from app.domain.job_status import JobStatus
from app.models.job import Job
from app.repositories.job import JobRepository


class InvalidJobStatusTransitionError(ValueError):
    pass


async def _transition_job_status(
    repository: JobRepository,
    *,
    job_id: int,
    allowed_from: set[JobStatus],
    target_status: JobStatus,
) -> Job:
    job = await repository.get_job_by_id(job_id)

    if job is None:
        raise ValueError("job not found")

    current_status = JobStatus(job.status)

    if current_status not in allowed_from:
        raise InvalidJobStatusTransitionError(
            f"cannot move job {job_id} from {current_status} to {target_status}"
        )

    return await repository.update_job_status(
        job_id=job_id,
        status=target_status,
        updated_at=datetime.now(UTC),
    )


async def start_job(repository: JobRepository, *, job_id: int) -> Job:
    return await _transition_job_status(
        repository,
        job_id=job_id,
        allowed_from={JobStatus.ASSIGNED},
        target_status=JobStatus.IN_PROGRESS,
    )


async def complete_job(repository: JobRepository, *, job_id: int) -> Job:
    return await _transition_job_status(
        repository,
        job_id=job_id,
        allowed_from={JobStatus.IN_PROGRESS},
        target_status=JobStatus.COMPLETED,
    )


async def confirm_assignment(repository: JobRepository, *, job_id: int) -> Job:
    return await _transition_job_status(
        repository,
        job_id=job_id,
        allowed_from={JobStatus.ASSIGNED_PENDING_CONFIRMATION},
        target_status=JobStatus.ASSIGNED,
    )


async def reopen_assignment_search(repository: JobRepository, *, job_id: int) -> Job:
    await repository.clear_assignment_confirmation_statuses(
        job_id=job_id,
        updated_at=datetime.now(UTC),
    )
    return await _transition_job_status(
        repository,
        job_id=job_id,
        allowed_from={JobStatus.ASSIGNED_PENDING_CONFIRMATION},
        target_status=JobStatus.READY_FOR_MATCHING,
    )


async def cancel_job(repository: JobRepository, *, job_id: int) -> Job:
    return await _transition_job_status(
        repository,
        job_id=job_id,
        allowed_from={
            JobStatus.READY_FOR_MATCHING,
            JobStatus.MATCHING,
            JobStatus.OFFERED,
            JobStatus.ASSIGNED_PENDING_CONFIRMATION,
            JobStatus.ASSIGNED,
            JobStatus.IN_PROGRESS,
        },
        target_status=JobStatus.CANCELLED,
    )
