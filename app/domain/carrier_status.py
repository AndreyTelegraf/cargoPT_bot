from enum import StrEnum


class CarrierStatus(StrEnum):
    DRAFT = "draft"
    INVITED = "invited"
    ACTIVE = "active"
    PROFILE_COMPLETED = "profile_completed"
