from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.job_request import JobRequestStates
from app.db.session import async_session_maker
from app.repositories.job import JobRepository
from app.services.job import JobService
from app.repositories.carrier import CarrierRepository
from app.services.carrier_search import CarrierSearchService
from app.services.job_matching import JobMatchingService
from app.services.job_offer import JobOfferService
from app.services.offer_distribution import OfferDistributionService

router = Router()


@router.message(JobRequestStates.comment)
async def job_comment(
    message: Message,
    state: FSMContext,
) -> None:
    raw_comment = (message.text or "").strip()
    comment = None if raw_comment in {"", "-"} else raw_comment

    data = await state.get_data()
    job_id = data["job_id"]

    async with async_session_maker() as session:
        job_repository = JobRepository(session)
        carrier_repository = CarrierRepository(session)
        job_service = JobService(job_repository)

        job = await job_service.finalize_for_matching(
            job_id=job_id,
            comment=comment,
        )

        distribution = OfferDistributionService(
            matching_service=JobMatchingService(
                CarrierSearchService(carrier_repository)
            ),
            offer_service=JobOfferService(job_repository),
            job_repository=job_repository,
        )

        offers = await distribution.create_offers_for_job(
            job,
            limit=5,
            expires_in_minutes=60,
        )

        await session.commit()

    await state.clear()

    await message.answer(
        f"Заявка сохранена. Подходящих перевозчиков найдено: {len(offers)}."
    )
