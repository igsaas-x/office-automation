from dataclasses import dataclass
from typing import Optional

@dataclass
class CheckInRequest:
    employee_id: int
    group_id: int
    latitude: float
    longitude: float
    photo_url: Optional[str] = None

@dataclass
class CheckInResponse:
    success: bool
    message: str
    timestamp: str
    location: str
