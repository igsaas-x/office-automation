from dataclasses import dataclass
from datetime import datetime, date, timezone
from typing import Optional

@dataclass
class FuelRecord:
    id: Optional[int]
    group_id: int
    vehicle_id: int
    date: date
    liters: float
    cost: float
    receipt_photo_url: Optional[str]
    created_at: datetime

    @classmethod
    def create(
        cls,
        group_id: int,
        vehicle_id: int,
        fuel_date: date,
        liters: float,
        cost: float,
        receipt_photo_url: Optional[str] = None
    ) -> 'FuelRecord':
        return cls(
            id=None,
            group_id=group_id,
            vehicle_id=vehicle_id,
            date=fuel_date,
            liters=liters,
            cost=cost,
            receipt_photo_url=receipt_photo_url,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
