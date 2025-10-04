from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class EmployeeGroup:
    """Association between Employee and Group"""
    id: Optional[int]
    employee_id: int
    group_id: int
    joined_at: datetime

    @classmethod
    def create(cls, employee_id: int, group_id: int) -> 'EmployeeGroup':
        return cls(
            id=None,
            employee_id=employee_id,
            group_id=group_id,
            joined_at=datetime.utcnow()
        )
