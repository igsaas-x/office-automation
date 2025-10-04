from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from ..value_objects.location import Location

@dataclass
class CheckIn:
    id: Optional[int]
    employee_id: int
    location: Location
    timestamp: datetime

    @classmethod
    def create(cls, employee_id: int, location: Location) -> 'CheckIn':
        return cls(
            id=None,
            employee_id=employee_id,
            location=location,
            timestamp=datetime.utcnow()
        )
