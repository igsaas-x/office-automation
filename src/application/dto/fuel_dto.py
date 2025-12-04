from dataclasses import dataclass
from typing import Optional

@dataclass
class RecordFuelRequest:
    group_id: int
    vehicle_id: int
    liters: float
    cost: float
    receipt_photo_url: Optional[str] = None

@dataclass
class FuelResponse:
    id: int
    group_id: int
    vehicle_id: int
    date: str
    liters: float
    cost: float
    receipt_photo_url: Optional[str]
    created_at: str
    vehicle_license_plate: str = None  # For display purposes
