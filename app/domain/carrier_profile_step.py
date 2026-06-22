from enum import StrEnum


class CarrierProfileStep(StrEnum):
    ASSEMBLY_REQUIRED = "assembly_required"
    PACKING_REQUIRED = "packing_required"
    OPERATING_REGIONS = "operating_regions"
    VEHICLES = "vehicles"
    COMPLETED = "completed"
