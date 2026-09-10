from aiogram.types import InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup

from app.bot.offer_locale import decline_reason_text
from app.bot.offer_locale import offer_text as t
from app.domain.job_decline_reason import DECLINE_REASONS


def build_assignment_confirmation_keyboard(
    job_id: int,
    locale: str | None = None,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(locale, "assignment_confirm"),
                    callback_data=f"assignment:confirm:{job_id}",
                ),
                InlineKeyboardButton(
                    text=t(locale, "assignment_fail"),
                    callback_data=f"assignment:fail:{job_id}",
                ),
            ]
        ]
    )


def build_assignment_failure_reason_keyboard(
    job_id: int,
    locale: str | None = None,
) -> InlineKeyboardMarkup:
    rows = []

    for index in range(0, len(DECLINE_REASONS), 2):
        rows.append(
            [
                InlineKeyboardButton(
                    text=decline_reason_text(locale, reason.code),
                    callback_data=f"assignment:fail_reason:{job_id}:{reason.code}",
                )
                for reason in DECLINE_REASONS[index:index + 2]
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=rows)

def build_client_reopen_assignment_keyboard(job_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Не договорились с перевозчиком",
                    callback_data=f"assignment:fail_reason:{job_id}:unspecified",
                ),
            ],
        ]
    )
