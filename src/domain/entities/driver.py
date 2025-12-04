from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

@dataclass
class Driver:
    id: Optional[int]
    group_id: int
    name: str
    phone: str
    role: str  # Defaults to DRIVER in Phase 1
    assigned_vehicle_id: Optional[int]
    created_at: datetime

    @classmethod
    def create(
        cls,
        group_id: int,
        name: str,
        phone: str,
        assigned_vehicle_id: Optional[int] = None,
        role: str = 'DRIVER'
    ) -> 'Driver':
        return cls(
            id=None,
            group_id=group_id,
            name=name,
            phone=phone,
            role=role,
            assigned_vehicle_id=assigned_vehicle_id,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
