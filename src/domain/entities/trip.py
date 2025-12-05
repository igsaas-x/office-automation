from dataclasses import dataclass
from datetime import datetime, date, timezone
from typing import Optional

@dataclass
class Trip:
    id: Optional[int]
    group_id: int
    vehicle_id: int
    driver_id: int
    date: date
    trip_number: int  # Auto-increments daily per vehicle
    loading_size_cubic_meters: Optional[float]  # Loading size in cubic meters
    created_at: datetime

    @classmethod
    def create(
        cls,
        group_id: int,
        vehicle_id: int,
        driver_id: int,
        trip_date: date,
        trip_number: int,
        loading_size_cubic_meters: Optional[float] = None
    ) -> 'Trip':
        return cls(
            id=None,
            group_id=group_id,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            date=trip_date,
            trip_number=trip_number,
            loading_size_cubic_meters=loading_size_cubic_meters,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
