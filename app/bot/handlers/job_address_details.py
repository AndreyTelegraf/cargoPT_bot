import re

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.job_request_keyboards import support_keyboard
from app.bot.states.job_request import JobRequestStates
from app.db.session import async_session_maker
from app.repositories.job import JobRepository
from app.services.job import JobService

router = Router()


_FLOOR_WORDS = {
    "подвал": -1,
    "минус первый": -1,
    "цоколь": -1,
    "cave": -1,
    "rés do chão": 0,
    "res do chao": 0,
    "rés-do-chão": 0,
    "res-do-chao": 0,
    "ground floor": 0,
    "ground": 0,
    "нулевой": 0,
    "нулевом": 0,
    "primeiro": 1,
    "первый": 1,
    "первом": 1,
    "второй": 2,
    "втором": 2,
    "третий": 3,
    "третьем": 3,
    "четвертый": 4,
    "четвёртый": 4,
    "четвертом": 4,
    "четвёртом": 4,
    "пятый": 5,
    "пятом": 5,
    "шестой": 6,
    "шестом": 6,
    "седьмой": 7,
    "седьмом": 7,
    "восьмой": 8,
    "восьмом": 8,
    "девятый": 9,
    "девятом": 9,
    "десятый": 10,
    "десятом": 10,
}


def _normalize_floor_elevator_text(raw_text: str) -> str:
    text = raw_text.strip().casefold().replace("ё", "е")
    text = text.replace("não", "nao")
    text = re.sub(r"[;,.:()\[\]{}]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_floor(text: str) -> int:
    if not text:
        raise ValueError("empty details")

    if re.search(r"(?<!\w)(r\s*/\s*c|rc)(?!\w)", text):
        return 0

    explicit_patterns = [
        r"(?:этаж|етаж|floor|andar|piso)\s*(?:№|#|nº|n\.|:|-)?\s*(-?\d+)",
        r"(-?\d+)\s*(?:й|ой|ый|ом|º|°)?\s*(?:этаж|етаж|floor|andar|piso)",
        r"(?:на|ao|no)\s*(-?\d+)\s*(?:й|ой|ый|ом|º|°)?",
    ]

    for pattern in explicit_patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))

    for word, value in sorted(_FLOOR_WORDS.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(rf"(?<!\w){re.escape(word)}(?!\w)", text):
            return value

    match = re.search(r"(?<!\d)-?\d+(?!\d)", text)
    if match:
        return int(match.group(0))

    raise ValueError("invalid floor")


def _parse_elevator(text: str) -> bool | None:
    negative_patterns = [
        r"нет\s+лифт\w*",
        r"лифт\w*\s+нет",
        r"без\s+лифт\w*",
        r"no\s+elevator",
        r"without\s+elevator",
        r"sem\s+elevador",
        r"nao\s+tem\s+elevador",
        r"elevador\s+nao",
        r"лифт\w*\s*[-—]\s*нет",
    ]

    positive_patterns = [
        r"есть\s+лифт\w*",
        r"лифт\w*\s+есть",
        r"с\s+лифт\w*",
        r"with\s+elevator",
        r"com\s+elevador",
        r"tem\s+elevador",
        r"elevador\s+sim",
        r"лифт\w*\s*[-—]\s*да",
    ]

    for pattern in negative_patterns:
        if re.search(pattern, text):
            return False

    for pattern in positive_patterns:
        if re.search(pattern, text):
            return True

    parts = [part.strip() for part in re.split(r"[,;]", text) if part.strip()]
    tail = " ".join(parts[1:]) if len(parts) > 1 else text

    positive_words = {"да", "yes", "y", "+", "есть", "sim"}
    negative_words = {"нет", "no", "n", "-", "sem", "nao"}

    tokens = set(tail.split())
    if tokens & negative_words:
        return False
    if tokens & positive_words:
        return True

    return None


def _parse_floor_elevator(raw_text: str) -> tuple[int | None, bool | None]:
    text = _normalize_floor_elevator_text(raw_text)
    floor = _parse_floor(text)
    has_elevator = _parse_elevator(text)
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
