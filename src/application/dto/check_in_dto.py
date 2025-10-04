from dataclasses import dataclass

@dataclass
class CheckInRequest:
    employee_id: int
    latitude: float
    longitude: float

@dataclass
class CheckInResponse:
    success: bool
    message: str
    timestamp: str
    location: str
