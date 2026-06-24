from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton
from aiogram.types import Message
from aiogram.types import ReplyKeyboardMarkup

from app.bot.states.carrier_onboarding import CarrierOnboardingStates

from app.db.session import async_session_maker
from app.repositories.carrier import CarrierRepository
from app.services.carrier_vehicle import CarrierVehicleService

router = Router()


def submit_moderation_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отправить на модерацию")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def _format_bool(value: bool | None) -> str:
    return "Да" if value else "Нет"


def build_carrier_preview_text(data: dict) -> str:
    return (
        "Проверьте анкету перевозчика перед отправкой на модерацию.\n\n"
        f"Сборка/разборка мебели: {_format_bool(data.get('assembly_required'))}\n"
        f"Упаковка груза: {_format_bool(data.get('packing_required'))}\n"
        f"Регионы работы: {data.get('operating_regions', 'не указано')}\n\n"
        "Автомобиль 1\n"
        f"Тип: {data.get('vehicle_type', 'не указано')}\n"
        f"Грузоподъёмность: {data.get('payload_kg', 'не указано')} кг\n"
        f"Объём: {data.get('volume_m3', 'не указано')} м³\n"
        f"Гидроборт: {_format_bool(data.get('has_tail_lift'))}\n"
        f"Кран: {_format_bool(data.get('has_crane'))}\n"
        f"Мобильный лифт: {_format_bool(data.get('has_mobile_lift'))}\n"
        f"Макс. этаж мобильного лифта: {data.get('mobile_lift_max_floor', 'не указано')}\n"
        f"Макс. вес мобильного лифта: {data.get('mobile_lift_max_weight_kg', 'не указано')} кг\n"
        f"Макс. вес крана: {data.get('crane_max_weight_kg', 'не указано')} кг\n"
        f"Вылет стрелы крана: {data.get('crane_max_reach_m', 'не указано')} м\n\n"
        f"Сотрудников: {data.get('employee_count', 'не указано')}\n"
        f"Макс. грузчиков на заказ: {data.get('max_loaders', 'не указано')}\n"
        f"Телефон: {data.get('company_phone', 'не указано')}\n"
        f"Email: {data.get('company_email', 'не указано')}\n\n"
        "Если всё верно, нажмите «Отправить на модерацию»."
    )


@router.message(CarrierOnboardingStates.company_email)
async def company_email(
    message: Message,
    state: FSMContext,
) -> None:

    email = message.text.strip()

    if "@" not in email or "." not in email:
        await message.answer("Укажите корректный email компании.")
        return

    await state.update_data(
        company_email=email
    )

    data = await state.get_data()
    carrier_id = data["carrier_id"]

    async with async_session_maker() as session:
        repository = CarrierRepository(session)
        service = CarrierVehicleService(repository)

        existing_vehicles = await repository.list_vehicles_by_carrier(carrier_id)

        if not existing_vehicles:
            await service.create_vehicle(
                carrier_id=carrier_id,
                vehicle_type=data["vehicle_type"],
                payload_kg=data["payload_kg"],
                volume_m3=data["volume_m3"],
                has_tail_lift=data["has_tail_lift"],
                has_crane=data["has_crane"],
                has_mobile_lift=data["has_mobile_lift"],
                mobile_lift_max_floor=data.get("mobile_lift_max_floor"),
                mobile_lift_max_weight_kg=data.get("mobile_lift_max_weight_kg"),
                crane_max_weight_kg=data.get("crane_max_weight_kg"),
                crane_reach_meters=data.get("crane_max_reach_m"),
            )

        await session.commit()

    await state.set_state(CarrierOnboardingStates.moderation_review)

    await message.answer(
        build_carrier_preview_text(data),
        reply_markup=submit_moderation_keyboard(),
    )
