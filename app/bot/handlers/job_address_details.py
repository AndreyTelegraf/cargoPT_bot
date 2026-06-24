from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.job_request_keyboards import support_keyboard
from app.bot.states.job_request import JobRequestStates
from app.db.session import async_session_maker
from app.repositories.job import JobRepository
from app.services.job import JobService

router = Router()


def _parse_floor_elevator(raw_text: str) -> tuple[int | None, bool | None]:
    text = raw_text.strip().casefold()
    if not text:
        raise ValueError("empty details")

    parts = [part.strip() for part in text.replace(";", ",").split(",") if part.strip()]
    if not parts:
        raise ValueError("empty details")

    try:
        floor = int(parts[0])
    except ValueError as exc:
        raise ValueError("invalid floor") from exc

    has_elevator = None
    rest = " ".join(parts[1:])

    if rest:
        positive = {"да", "yes", "y", "+", "есть", "sim"}
        negative = {"нет", "no", "n", "-", "sem", "nao", "não"}

        if rest in positive:
            has_elevator = True
        elif rest in negative:
            has_elevator = False
        else:
            raise ValueError("invalid elevator")

    return floor, has_elevator


async def _save_details(
    message: Message,
    state: FSMContext,
    *,
    address_id_key: str,
    next_state,
    next_text: str,
    next_reply_markup=None,
) -> None:
    try:
        floor, has_elevator = _parse_floor_elevator(message.text or "")
    except ValueError:
        await message.answer(
            "Не понял этаж и лифт. Напишите в формате: этаж, лифт да/нет.\n"
            "Примеры: 2, да; 0, нет; -1, да",
            reply_markup=support_keyboard(),
        )
        return

    data = await state.get_data()
    address_id = data[address_id_key]

    async with async_session_maker() as session:
        repository = JobRepository(session)
        service = JobService(repository)

        await service.update_address_details(
            address_id=address_id,
            floor=floor,
            has_elevator=has_elevator,
        )

        await session.commit()

    await state.set_state(next_state)
    await message.answer(next_text, reply_markup=next_reply_markup)


@router.message(JobRequestStates.pickup_details)
async def pickup_details(message: Message, state: FSMContext) -> None:
    await _save_details(
        message,
        state,
        address_id_key="pickup_address_id",
        next_state=JobRequestStates.dropoff_address,
        next_text=(
            "Теперь место выгрузки.\n\n"
            "Вставьте ссылку на точку из Google Maps или введите полный адрес, "
            "например Rua Escura, 1, Porto, 4050-242"
        ),
        next_reply_markup=support_keyboard(),
    )


@router.message(JobRequestStates.dropoff_details)
async def dropoff_details(message: Message, state: FSMContext) -> None:
    from app.bot.job_request_keyboards import datetime_keyboard

    await _save_details(
        message,
        state,
        address_id_key="dropoff_address_id",
        next_state=JobRequestStates.requested_datetime,
        next_text=(
            "Когда нужна перевозка?\n\n"
            "Выберите быстрый вариант или напишите дату и время вручную.\n"
            "Примеры: 24.06 10:00, 24.06.2026 15:30.\n"
            "Если точное время пока не важно — напишите только дату."
        ),
        next_reply_markup=datetime_keyboard(),
    )
