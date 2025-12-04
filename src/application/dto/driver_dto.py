from dataclasses import dataclass
from typing import Optional

@dataclass
class RegisterDriverRequest:
    group_id: int
    name: str
    phone: str
    assigned_vehicle_id: Optional[int] = None
    role: str = 'DRIVER'  # Defaults to DRIVER in Phase 1

@dataclass
class DriverResponse:
    id: int
    group_id: int
    name: str
    phone: str
    role: str
    assigned_vehicle_id: Optional[int]
    created_at: str
