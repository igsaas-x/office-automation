from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

@dataclass
class Allowance:
    id: Optional[int]
    employee_id: int
    amount: float
    allowance_type: str
    note: Optional[str]
    created_by: str
    timestamp: datetime

    @classmethod
    def create(
        cls,
        employee_id: int,
        amount: float,
        allowance_type: str,
        created_by: str,
        note: Optional[str] = None
    ) -> 'Allowance':
        return cls(
            id=None,
            employee_id=employee_id,
            amount=amount,
            allowance_type=allowance_type,
            note=note,
            created_by=created_by,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
