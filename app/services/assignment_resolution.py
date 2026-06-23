from dataclasses import dataclass

from app.domain.job_status import JobStatus
from app.repositories.carrier import CarrierRepository
from app.repositories.job import JobRepository
from app.services.assignment_confirmation import ASSIGNMENT_CONFIRMATION_CONFIRMED
from app.services.assignment_confirmation import ASSIGNMENT_CONFIRMATION_FAILED
from app.services.assignment_confirmation import record_assignment_confirmation
from app.services.carrier_search import CarrierSearchService
from app.services.job import JobService
from app.services.job_matching import JobMatchingService
from app.services.job_offer import JobOfferService
from app.services.offer_distribution import OfferDistributionService
from app.services.offer_notification import send_job_offers_to_carriers


@dataclass(frozen=True)
class AssignmentResolutionResult:
    message: str
    should_delete_carrier_offer: bool
    carrier_message_chat_id: int | None
    carrier_message_id: int | None


async def _resolve_assignment_actor(
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


def _build_result_text(*, job_id: int, action: str, job_status: str) -> str:
    if job_status == JobStatus.ASSIGNED:
        return f"Сделка по заявке №{job_id} подтверждена обеими сторонами."

    if job_status == JobStatus.READY_FOR_MATCHING:
        return (
            f"По заявке №{job_id} сделка не состоялась. "
            "Заявка возвращена в активный поиск."
        )

    if action == "confirm":
        return (
            f"Ваше подтверждение по заявке №{job_id} принято. "
            "Ждём ответ второй стороны."
        )

    return (
        f"Ваш ответ по заявке №{job_id} принят. "
        "Заявка будет возвращена в активный поиск."
    )


async def process_assignment_decision(
    *,
    bot,
    telegram_user_id: int,
    job_id: int,
    action: str,
    job_repository: JobRepository,
    carrier_repository: CarrierRepository,
    job_service: JobService,
) -> AssignmentResolutionResult | None:
    job = await job_repository.get_job_by_id(job_id)
    accepted_offer = await job_repository.get_accepted_offer_by_job_id(job_id)

    if job is None:
        return None

    actor = await _resolve_assignment_actor(
        telegram_user_id=telegram_user_id,
        job=job,
        accepted_offer=accepted_offer,
        carrier_repository=carrier_repository,
    )

    if actor is None:
        return None

    confirmation_status = (
        ASSIGNMENT_CONFIRMATION_CONFIRMED
        if action == "confirm"
        else ASSIGNMENT_CONFIRMATION_FAILED
    )

    updated_job = await record_assignment_confirmation(
        job_service,
        job_id=job_id,
        actor=actor,
        status=confirmation_status,
    )

    should_delete_carrier_offer = updated_job.status == JobStatus.READY_FOR_MATCHING
    carrier_message_chat_id = (
        accepted_offer.carrier_message_chat_id if accepted_offer is not None else None
    )
    carrier_message_id = (
        accepted_offer.carrier_message_id if accepted_offer is not None else None
    )

    if should_delete_carrier_offer:
        distribution = OfferDistributionService(
            matching_service=JobMatchingService(
                CarrierSearchService(carrier_repository)
            ),
            offer_service=JobOfferService(job_repository),
            job_repository=job_repository,
        )
        new_offers = await distribution.create_offers_for_job(
            updated_job,
            limit=5,
            expires_in_minutes=60,
        )
        await send_job_offers_to_carriers(
            bot=bot,
            job=updated_job,
            offers=new_offers,
            job_repository=job_repository,
            carrier_repository=carrier_repository,
        )

    return AssignmentResolutionResult(
        message=_build_result_text(
            job_id=job_id,
            action=action,
            job_status=updated_job.status,
        ),
        should_delete_carrier_offer=should_delete_carrier_offer,
        carrier_message_chat_id=carrier_message_chat_id,
        carrier_message_id=carrier_message_id,
    )
