from aiogram.types import InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup


def build_offer_keyboard(offer_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять",
                    callback_data=f"offer:accept:{offer_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"offer:decline:{offer_id}",
                ),
            ]
        ]
    )
