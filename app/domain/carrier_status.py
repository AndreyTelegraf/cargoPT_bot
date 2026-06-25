from enum import StrEnum


class CarrierStatus(StrEnum):
    DRAFT = "draft"
    INVITED = "invited"
    PENDING_MODERATION = "pending_moderation"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REJECTED = "rejected"
    PROFILE_COMPLETED = "profile_completed"
