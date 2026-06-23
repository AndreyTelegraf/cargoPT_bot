from enum import StrEnum


class JobStatus(StrEnum):
    DRAFT = "draft"
    READY_FOR_MATCHING = "ready_for_matching"
    MATCHING = "matching"
    OFFERED = "offered"
    UNMATCHED = "unmatched"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
