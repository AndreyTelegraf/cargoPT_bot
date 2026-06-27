from dataclasses import dataclass


@dataclass(frozen=True)
class DeclineReason:
    code: str
    label: str


DECLINE_REASONS = (
    DeclineReason("time_unavailable", "Не подошло время"),
    DeclineReason("price_not_agreed", "Не договорились по цене"),
    DeclineReason("outside_area", "Не подходит зона"),
    DeclineReason("wrong_vehicle", "Нужна другая машина"),
    DeclineReason("no_loaders", "Нет грузчиков"),
    DeclineReason("route_or_floor_issue", "Маршрут/этажи не подходят"),
    DeclineReason("client_unreachable", "Клиент не вышел на связь"),
    DeclineReason("other", "Другое"),
)


DECLINE_REASON_LABELS = {
    reason.code: reason.label
    for reason in DECLINE_REASONS
}


UNSPECIFIED_DECLINE_REASON = "unspecified"


def is_valid_decline_reason(value: str) -> bool:
    return value in DECLINE_REASON_LABELS or value == UNSPECIFIED_DECLINE_REASON


def get_decline_reason_label(value: str | None) -> str:
    if value is None:
        return "Не указано"
    if value == UNSPECIFIED_DECLINE_REASON:
        return "Не указано"
    return DECLINE_REASON_LABELS.get(value, value)
