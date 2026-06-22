from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from app.bot.offer_keyboard import build_offer_keyboard

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

        media_items = await job_repository.list_media_by_job(job.id)

        sent_count = 0

        for offer in offers:
            carrier = await carrier_repository.get_carrier_by_vehicle_id(
                offer.vehicle_id
            )

            if carrier is None or carrier.telegram_user_id is None:
                continue

            await message.bot.send_message(
                chat_id=carrier.telegram_user_id,
                text=(
                    "Новая заявка на перевозку.\\n"
                    f"Заявка #{job.id}.\\n"
                    "Нажмите кнопку, чтобы принять или отказаться."
                ),
                reply_markup=build_offer_keyboard(offer.id),
            )

            for media in media_items:
                caption = media.caption or f"Медиа к заявке #{job.id}"

                if media.media_type == "photo":
                    await message.bot.send_photo(
                        chat_id=carrier.telegram_user_id,
                        photo=media.telegram_file_id,
                        caption=caption,
                    )
                elif media.media_type == "video":
                    await message.bot.send_video(
                        chat_id=carrier.telegram_user_id,
                        video=media.telegram_file_id,
                        caption=caption,
                    )

            sent_count += 1

        await session.commit()

    await state.clear()

    await message.answer(
        f"Заявка сохранена. Офферы отправлены перевозчикам: {sent_count}."
    )
