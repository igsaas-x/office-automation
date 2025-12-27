from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from ..value_objects.location import Location
from ..value_objects.check_in_type import CheckInType

@dataclass
class CheckIn:
    id: Optional[int]
    employee_id: int
    group_id: int
    location: Location
    timestamp: datetime
    type: CheckInType = CheckInType.CHECKIN
    photo_url: Optional[str] = None

    @classmethod
    def create(cls, employee_id: int, group_id: int, location: Location, type: CheckInType = CheckInType.CHECKIN, photo_url: Optional[str] = None) -> 'CheckIn':
        return cls(
            id=None,
            employee_id=employee_id,
            group_id=group_id,
            location=location,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
            type=type,
            photo_url=photo_url
        )
