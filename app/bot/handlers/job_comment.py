from datetime import UTC
from datetime import datetime
from datetime import timedelta

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.job_request_keyboards import support_keyboard
from app.bot.states.job_request import JobRequestStates
from app.db.session import async_session_maker
from app.repositories.carrier import CarrierRepository
from app.repositories.job import JobRepository
from app.services.carrier_search import CarrierSearchService
from app.services.job import JobService
from app.services.job_matching import JobMatchingService
from app.services.job_offer import JobOfferService
from app.services.offer_distribution import OfferDistributionService
from app.services.offer_notification import send_job_offers_to_carriers

router = Router()


@router.message(JobRequestStates.comment)
async def job_comment(
    message: Message,
    state: FSMContext,
) -> None:
    raw_comment = (message.text or "").strip()
    comment = None if raw_comment in {"", "-", "Без комментария"} else raw_comment

    data = await state.get_data()
    job_id = data["job_id"]

    async with async_session_maker() as session:
        job_repository = JobRepository(session)
        carrier_repository = CarrierRepository(session)
        job_service = JobService(job_repository)

        active_jobs = await job_repository.count_active_client_jobs(
            message.from_user.id
        )
        if active_jobs >= 2:
            await message.answer(
                "У вас уже есть 2 активные заявки. "
                "Дождитесь ответа по одной из них или отмените лишнюю через диспетчера: https://t.me/andreytelegraf"
            )
            await session.rollback()
            return

        sent_since = datetime.now(UTC) - timedelta(hours=24)
        sent_jobs = await job_repository.count_sent_client_jobs_since(
            message.from_user.id,
            sent_since,
        )
        if sent_jobs >= 3:
            await message.answer(
                "Лимит CargoPT: не больше 3 отправленных заявок за 24 часа. "
                "Попробуйте позже или напишите диспетчеру: https://t.me/andreytelegraf"
            )
            await session.rollback()
            return

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

        sent_count = await send_job_offers_to_carriers(
            bot=message.bot,
            job=job,
            offers=offers,
            job_repository=job_repository,
            carrier_repository=carrier_repository,
        )

        await session.commit()

    await state.clear()

    if sent_count > 0:
        await message.answer(
            "Заявка опубликована.\n\n"
            f"Мы отправили её подходящим перевозчикам: {sent_count}. "
            "Как только кто-то примет заказ, вы получите уведомление.",
            reply_markup=support_keyboard(),
        )
    else:
        await message.answer(
            "Заявка опубликована.\n\n"
            "Сейчас в системе нет подходящих перевозчиков. "
            "Диспетчер CargoPT проверит заявку вручную.",
            reply_markup=support_keyboard(),
        )
