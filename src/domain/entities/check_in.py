from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from ..value_objects.location import Location

@dataclass
class CheckIn:
    id: Optional[int]
    employee_id: int
    group_id: int
    location: Location
    timestamp: datetime
    photo_url: Optional[str] = None

    @classmethod
    def create(cls, employee_id: int, group_id: int, location: Location, photo_url: Optional[str] = None) -> 'CheckIn':
        return cls(
            id=None,
            employee_id=employee_id,
            group_id=group_id,
            location=location,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
            photo_url=photo_url
        )
