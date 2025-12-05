from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

@dataclass
class Vehicle:
    id: Optional[int]
    group_id: int
    license_plate: str
    vehicle_type: str  # TRUCK, VAN, MOTORCYCLE, CAR
    driver_name: Optional[str]  # Optional driver name
    created_at: datetime

    @classmethod
    def create(
        cls,
        group_id: int,
        license_plate: str,
        vehicle_type: str,
        driver_name: Optional[str] = None
    ) -> 'Vehicle':
        return cls(
            id=None,
            group_id=group_id,
            license_plate=license_plate,
            vehicle_type=vehicle_type,
            driver_name=driver_name,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
