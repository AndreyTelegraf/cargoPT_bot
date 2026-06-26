from aiogram.types import KeyboardButton
from aiogram.types import ReplyKeyboardMarkup


def _keyboard(rows: list[list[str]], *, include_help: bool = True) -> ReplyKeyboardMarkup:
    keyboard_rows = list(rows)
    if include_help:
        keyboard_rows.append(["Помощь"])

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=value) for value in row]
            for row in keyboard_rows
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def support_keyboard() -> ReplyKeyboardMarkup:
    return _keyboard([], include_help=True)


def client_start_keyboard() -> ReplyKeyboardMarkup:
    return support_keyboard()


def yes_no_keyboard() -> ReplyKeyboardMarkup:
    return _keyboard([["Да", "Нет"]])



def floor_keyboard() -> ReplyKeyboardMarkup:
    floors = [str(value) for value in range(0, 25)]
    rows = [floors[index:index + 5] for index in range(0, len(floors), 5)]
    rows.append(["Подвал"])
    return _keyboard(rows)


def elevator_keyboard() -> ReplyKeyboardMarkup:
    return _keyboard([["Да", "Нет"]])


def payload_keyboard() -> ReplyKeyboardMarkup:
    return _keyboard([
        ["до 500 кг", "до 1000 кг"],
        ["до 1600 кг", "до 3500 кг"],
        ["Не знаю"],
    ])


def volume_keyboard() -> ReplyKeyboardMarkup:
    return _keyboard([
        ["до 3 м³", "до 10 м³"],
        ["до 18 м³", "до 35 м³"],
        ["Не знаю"],
    ])


def loaders_keyboard() -> ReplyKeyboardMarkup:
    return _keyboard([
        ["0", "1", "2"],
        ["3", "4+"],
        ["Не знаю"],
    ])


def media_skip_keyboard() -> ReplyKeyboardMarkup:
    return _keyboard([["Следующий шаг"]])


def comment_skip_keyboard() -> ReplyKeyboardMarkup:
    return _keyboard([["Без комментария"]])


def username_ready_keyboard() -> ReplyKeyboardMarkup:
    return _keyboard([["Готово, username создан"]])


def phone_skip_keyboard() -> ReplyKeyboardMarkup:
    return _keyboard([["Не указывать телефон"]])


def whatsapp_keyboard() -> ReplyKeyboardMarkup:
    return _keyboard([
        ["WhatsApp совпадает"],
        ["Не указывать WhatsApp"],
    ])


def datetime_keyboard() -> ReplyKeyboardMarkup:
    return _keyboard([
        ["Сегодня", "Завтра"],
        ["В ближайшие дни"],
        ["Укажу дату текстом"],
    ])
