from dataclasses import dataclass
from typing import Optional

@dataclass
class RegisterVehicleRequest:
    group_id: int
    license_plate: str
    vehicle_type: str  # TRUCK, VAN, MOTORCYCLE, CAR

@dataclass
class VehicleResponse:
    id: int
    group_id: int
    license_plate: str
    vehicle_type: str
    created_at: str


@dataclass
class DeleteVehicleResponse:
    id: int
    license_plate: str
