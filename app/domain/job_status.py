from enum import StrEnum


class JobStatus(StrEnum):
    DRAFT = "draft"
    READY_FOR_MATCHING = "ready_for_matching"
    MATCHING = "matching"
    OFFERED = "offered"
    ASSIGNED = "assigned"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
