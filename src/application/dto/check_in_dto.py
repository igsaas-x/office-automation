from dataclasses import dataclass
from typing import Optional
from ...domain.value_objects.check_in_type import CheckInType

@dataclass
class CheckInRequest:
    employee_id: int
    group_id: int
    latitude: float
    longitude: float
    type: CheckInType = CheckInType.CHECKIN
    photo_url: Optional[str] = None

@dataclass
class CheckInResponse:
    success: bool
    message: str
    timestamp: str
    location: str
