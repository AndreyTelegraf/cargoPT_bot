from enum import StrEnum


class TelegramNotificationType(StrEnum):
    CARRIER_OFFER = "carrier_offer"
    MANUAL_REVIEW = "manual_review"


class TelegramDeliveryStatus(StrEnum):
    PENDING = "pending"
    SENDING = "sending"
    RETRY = "retry"
    SENT = "sent"
    FAILED = "failed"
