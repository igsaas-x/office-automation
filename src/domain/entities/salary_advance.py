from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from ..value_objects.money import Money

@dataclass
class SalaryAdvance:
    id: Optional[int]
    employee_id: int
    amount: Money
    note: Optional[str]
    created_by: str
    timestamp: datetime

    @classmethod
    def create(cls, employee_id: int, amount: Money, created_by: str, note: Optional[str] = None) -> 'SalaryAdvance':
        return cls(
            id=None,
            employee_id=employee_id,
            amount=amount,
            note=note,
            created_by=created_by,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
