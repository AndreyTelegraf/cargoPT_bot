from collections.abc import AsyncIterator

from aiogram import Bot
from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.web_request_schemas import WebRequestPayload
from app.api.web_request_schemas import WebRequestResponse
from app.config import settings
from app.db.session import async_session_maker
from app.repositories.carrier import CarrierRepository
from app.repositories.job import JobRepository
from app.services.web_intake import WebIntakeService


router = APIRouter()


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_api_bot() -> AsyncIterator[Bot]:
    bot = Bot(token=settings.bot_token)
    try:
        yield bot
    finally:
        await bot.session.close()


@router.post("/requests", response_model=WebRequestResponse)
async def submit_web_request(
    payload: WebRequestPayload,
    session: AsyncSession = Depends(get_session),
    bot: Bot = Depends(get_api_bot),
) -> WebRequestResponse:
    service = WebIntakeService(
        job_repository=JobRepository(session),
        carrier_repository=CarrierRepository(session),
        bot=bot,
    )
    result = await service.submit_web_request(payload.to_service_request())

    if result.job.id is None:
        raise RuntimeError("web request job id missing")

    return WebRequestResponse(
        job_id=result.job.id,
        status=str(result.job.status),
        offers_count=result.offers_count,
        sent_count=result.sent_count,
    )
