from dataclasses import dataclass

@dataclass
class RecordTripRequest:
    group_id: int
    vehicle_id: int
    driver_id: int

@dataclass
class TripResponse:
    id: int
    group_id: int
    vehicle_id: int
    driver_id: int
    date: str
    trip_number: int
    created_at: str
    vehicle_license_plate: str = None  # For display purposes
    driver_name: str = None  # For display purposes
