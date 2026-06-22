from datetime import UTC
from datetime import datetime

from app.models.carrier import CarrierVehicle
from app.repositories.carrier import CarrierRepository
from app.domain.vehicle_type import VehicleType


class CarrierVehicleService:
    def __init__(self, repository: CarrierRepository) -> None:
        self.repository = repository

    async def create_vehicle(
        self,
        *,
        carrier_id: int,
        vehicle_type: str,
        payload_kg: int | None,
        volume_m3: float | None,
        has_tail_lift: bool,
        has_crane: bool,
        has_mobile_lift: bool,
        mobile_lift_max_floor: int | None,
        mobile_lift_max_weight_kg: int | None,
        crane_max_weight_kg: int | None,
        crane_reach_meters: float | None,
    ) -> CarrierVehicle:
        now = datetime.now(UTC)

        vehicle = CarrierVehicle(
            carrier_id=carrier_id,
            vehicle_type=vehicle_type,
            payload_kg=payload_kg,
            volume_m3=volume_m3,
            has_tail_lift=has_tail_lift,
            has_crane=has_crane,
            has_mobile_lift=has_mobile_lift,
            mobile_lift_max_floor=mobile_lift_max_floor,
            mobile_lift_max_weight_kg=mobile_lift_max_weight_kg,
            crane_max_weight_kg=crane_max_weight_kg,
            crane_reach_meters=crane_reach_meters,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        return await self.repository.create_vehicle(vehicle)
