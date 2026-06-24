from aiogram import F
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.handlers.job_start import start_job_request
from app.db.session import async_session_maker
from app.domain.carrier_status import CarrierStatus
from app.repositories.carrier import CarrierRepository

router = Router()


def build_existing_carrier_start_text(carrier) -> str:
    if carrier.status == CarrierStatus.PENDING_MODERATION:
        return (
            "Вы уже зарегистрированы как перевозчик CargoPT.\n\n"
            "Ваша анкета отправлена на проверку.\n\n"
            "Когда она будет обработана, администратор свяжется с вами."
        )

    if carrier.status == CarrierStatus.ACTIVE:
        return (
            "Вы зарегистрированы как активный перевозчик CargoPT.\n\n"
            "Как это работает:\n"
            "- когда появится подходящий заказ, бот пришлёт вам предложение;\n"
            "- в предложении будут кнопки «Принять» и «Отказаться»;\n"
            "- после принятия заказа клиент должен подтвердить назначение.\n\n"
            "Сейчас ничего заполнять не нужно. Ожидайте новых заказов."
        )

    if carrier.status == CarrierStatus.PROFILE_COMPLETED:
        return (
            "Ваша анкета перевозчика уже заполнена.\n\n"
            "Если нужно что-то изменить, свяжитесь с администратором CargoPT."
        )

    return (
        "Вы уже привязаны к CargoPT как перевозчик.\n\n"
        "Если нужно создать клиентскую заявку на перевозку, используйте команду /new_job."
    )


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    async with async_session_maker() as session:
        repository = CarrierRepository(session)
        carrier = await repository.get_carrier_by_telegram_user_id(message.from_user.id)

    if carrier is not None and carrier.status != CarrierStatus.REJECTED:
        await state.clear()
        await message.answer(build_existing_carrier_start_text(carrier))
        return

    await start_job_request(message, state)


@router.message(F.text == "Помощь")
async def help_placeholder(message: Message) -> None:
    await message.answer(
        "Помощь скоро появится.\n\n"
        "Сейчас для создания заявки нажмите /start или /new_job."
    )


@router.message(F.text == "Мои объявления")
async def my_ads_placeholder(message: Message) -> None:
    await message.answer(
        "Раздел «Мои объявления» скоро появится.\n\n"
        "Сейчас активные заявки обрабатываются диспетчером CargoPT."
    )
