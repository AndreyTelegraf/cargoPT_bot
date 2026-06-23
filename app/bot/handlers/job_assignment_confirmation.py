from aiogram import F
from aiogram import Router
from aiogram.types import CallbackQuery

from app.db.session import async_session_maker
from app.domain.job_status import JobStatus
from app.repositories.carrier import CarrierRepository
from app.repositories.job import JobRepository
from app.services.job import InvalidJobStatusTransitionError
from app.services.job import JobService
from app.services.job import confirm_assignment
from app.services.job import reopen_assignment_search

router = Router()


def _parse_assignment_callback(data: str) -> tuple[str, int]:
    parts = data.split(":")
    if len(parts) != 3 or parts[0] != "assignment":
        raise ValueError("invalid callback data")

    action = parts[1]
    job_id = int(parts[2])

    if action not in {"confirm", "fail"}:
        raise ValueError("invalid assignment action")

    return action, job_id


async def _is_authorized_actor(
    *,
    telegram_user_id: int,
    job,
    accepted_offer,
    carrier_repository: CarrierRepository,
) -> bool:
    if job.client_telegram_user_id == telegram_user_id:
        return True

    carrier = await carrier_repository.get_carrier_by_telegram_user_id(telegram_user_id)
    if carrier is None or accepted_offer is None:
        return False

    return accepted_offer.carrier_id == carrier.id


@router.callback_query(F.data.startswith("assignment:"))
async def handle_assignment_confirmation(callback: CallbackQuery) -> None:
    try:
        action, job_id = _parse_assignment_callback(callback.data or "")
    except ValueError:
        await callback.answer("Некорректная кнопка", show_alert=True)
        return

    telegram_user_id = callback.from_user.id

    async with async_session_maker() as session:
        job_repository = JobRepository(session)
        carrier_repository = CarrierRepository(session)
        job_service = JobService(job_repository)

        job = await job_repository.get_job_by_id(job_id)
        accepted_offer = await job_repository.get_accepted_offer_by_job_id(job_id)

        if job is None:
            await callback.answer("Заявка не найдена.", show_alert=True)
            return

        is_authorized = await _is_authorized_actor(
            telegram_user_id=telegram_user_id,
            job=job,
            accepted_offer=accepted_offer,
            carrier_repository=carrier_repository,
        )

        if not is_authorized:
            await callback.answer("Эта кнопка не для вас.", show_alert=True)
            return

        if job.status != JobStatus.ASSIGNED_PENDING_CONFIRMATION:
            await callback.answer("Статус заявки уже изменён.", show_alert=True)
            return

        try:
            if action == "confirm":
                await confirm_assignment(job_service, job_id=job_id)
                result_text = f"Сделка по заявке №{job_id} подтверждена."
            else:
                await reopen_assignment_search(job_service, job_id=job_id)
                result_text = (
                    f"По заявке №{job_id} сделка не состоялась. "
                    "Заявка возвращена в активный поиск."
                )
        except InvalidJobStatusTransitionError:
            await session.rollback()
            await callback.answer("Статус заявки уже изменён.", show_alert=True)
            return

        await session.commit()

    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)

    await callback.answer(result_text, show_alert=True)
