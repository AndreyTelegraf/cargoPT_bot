from aiogram.types import InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup


def build_assignment_confirmation_keyboard(job_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Сделка подтверждена",
                    callback_data=f"assignment:confirm:{job_id}",
                ),
                InlineKeyboardButton(
                    text="Не договорились",
                    callback_data=f"assignment:fail:{job_id}",
                ),
            ]
        ]
    )
