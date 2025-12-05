from dataclasses import dataclass
from typing import Optional

@dataclass
class RecordTripRequest:
    group_id: int
    vehicle_id: int
    loading_size_cubic_meters: Optional[float] = None

@dataclass
class TripResponse:
    id: int
    group_id: int
    vehicle_id: int
    driver_name: Optional[str]  # Snapshot from vehicle at trip creation
    date: str
    trip_number: int
    loading_size_cubic_meters: Optional[float]
    created_at: str
    vehicle_license_plate: str = None  # For display purposes
