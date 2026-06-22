from enum import StrEnum


class VehicleType(StrEnum):
    SMALL_VAN = "small_van"
    MEDIUM_VAN = "medium_van"
    LARGE_VAN = "large_van"

    TRUCK_3_5T = "truck_3_5t"
    TRUCK_7_5T = "truck_7_5t"
    TRUCK_12T = "truck_12t"
    TRUCK_18T = "truck_18t"
    TRUCK_26T = "truck_26t"

    TOW_TRUCK = "tow_truck"
