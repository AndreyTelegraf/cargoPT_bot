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
from app.services.request_intake import RequestIntakeAddress
from app.services.request_intake import RequestIntakeInput
from app.services.request_intake import RequestIntakeItem
from app.services.request_intake import RequestIntakeService


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
    service_request = payload.to_service_request()
    service = RequestIntakeService(
        job_repository=JobRepository(session),
        carrier_repository=CarrierRepository(session),
        bot=bot,
    )
    result = await service.submit_web_intake(
        RequestIntakeInput(
            source_locale=service_request.source_locale,
            customer_name=service_request.customer_name,
            customer_email=service_request.customer_email,
            preferred_contact=service_request.preferred_contact,
            client_phone=service_request.client_phone,
            client_whatsapp=service_request.client_whatsapp,
            utm_source=service_request.utm_source,
            utm_campaign=service_request.utm_campaign,
            landing_version=service_request.landing_version,
            requested_date=service_request.requested_date,
            addresses=tuple(
                RequestIntakeAddress(
                    kind=address.kind,
                    raw_text=address.raw_text,
                    floor=address.floor,
                    has_elevator=address.has_elevator,
                )
                for address in service_request.addresses
            ),
            items=tuple(
                RequestIntakeItem(
                    description=item.description,
                    quantity=item.quantity,
                )
                for item in service_request.items
            ),
            needs_assembly=service_request.needs_assembly,
            needs_packing=service_request.needs_packing,
            needs_tail_lift=service_request.needs_tail_lift,
            needs_crane=service_request.needs_crane,
            needs_mobile_lift=service_request.needs_mobile_lift,
            required_loaders=service_request.required_loaders,
            estimated_payload_kg=service_request.estimated_payload_kg,
            estimated_volume_m3=service_request.estimated_volume_m3,
            comment=service_request.comment,
        )
    )

    if result.job.id is None:
        raise RuntimeError("web request job id missing")

    return WebRequestResponse(
        job_id=result.job.id,
        status=str(result.job.status),
        offers_count=result.offers_count,
        sent_count=result.sent_count,
    )
