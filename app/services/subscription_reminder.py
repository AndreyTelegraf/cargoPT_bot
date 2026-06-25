from datetime import UTC
from datetime import datetime
from datetime import timedelta

from app.repositories.carrier import CarrierRepository


def _normalize_dt(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def build_subscription_reminder_text(*, carrier, paid_until, days_left: int) -> str:
    paid_until_text = paid_until.strftime("%d.%m.%Y")

    if days_left < 0:
        return (
            "Напоминание от CargoPT.\n\n"
            f"Ваш оплаченный доступ к заявкам закончился {paid_until_text}. "
            "Сейчас компания не участвует в автоматической раздаче новых заявок.\n\n"
            "Чтобы снова получать заявки, продлите участие через администратора CargoPT."
        )

    if days_left == 0:
        return (
            "Напоминание от CargoPT.\n\n"
            f"Ваш оплаченный доступ к заявкам заканчивается сегодня, {paid_until_text}. "
            "После окончания срока компания автоматически перестанет получать новые заявки.\n\n"
            "Если хотите продолжить получать заявки без паузы, продлите участие через администратора CargoPT."
        )

    return (
        "Напоминание от CargoPT.\n\n"
        f"Ваш оплаченный доступ к заявкам действует до {paid_until_text}. "
        f"Осталось {days_left} дн.\n\n"
        "Если хотите продолжить получать заявки без паузы, продлите участие через администратора CargoPT."
    )


def build_subscription_reminder_marker(*, carrier_id: int, paid_until, days_left: int) -> str:
    paid_until_key = paid_until.date().isoformat()
    if days_left < 0:
        stage = "expired"
    elif days_left == 0:
        stage = "today"
    elif days_left <= 3:
        stage = "3d"
    else:
        stage = "7d"

    return f"[subscription_reminder:{carrier_id}:{paid_until_key}:{stage}]"


async def process_subscription_reminders(
    *,
    bot,
    session,
    horizon_days: int = 7,
) -> int:
    now = datetime.now(UTC)
    until = now + timedelta(days=horizon_days)

    repository = CarrierRepository(session)
    carriers = await repository.list_subscription_reminder_candidates(
        now=now,
        until=until,
    )

    sent_count = 0

    for carrier in carriers:
        paid_until = _normalize_dt(carrier.paid_until)
        if paid_until is None:
            continue

        days_left = (paid_until.date() - now.date()).days
        if days_left not in {7, 3, 1, 0} and days_left >= 0:
            continue

        marker = build_subscription_reminder_marker(
            carrier_id=carrier.id,
            paid_until=paid_until,
            days_left=days_left,
        )

        if marker in (carrier.internal_note or ""):
            continue

        text = build_subscription_reminder_text(
            carrier=carrier,
            paid_until=paid_until,
            days_left=days_left,
        )

        await bot.send_message(
            chat_id=carrier.telegram_user_id,
            text=text,
        )

        await repository.mark_subscription_reminder_sent(
            carrier_id=carrier.id,
            marker=marker,
            updated_at=now,
        )

        sent_count += 1

    return sent_count
