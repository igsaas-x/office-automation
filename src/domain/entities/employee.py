from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

@dataclass
class Employee:
    id: Optional[int]
    telegram_id: str
    name: str
    phone: Optional[str]
    role: Optional[str]
    date_start_work: Optional[datetime]
    probation_months: Optional[int]
    base_salary: Optional[float]
    bonus: Optional[float]
    created_at: datetime

    @classmethod
    def create(
        cls,
        telegram_id: str,
        name: str,
        phone: Optional[str] = None,
        role: Optional[str] = None,
        date_start_work: Optional[datetime] = None,
        probation_months: Optional[int] = None,
        base_salary: Optional[float] = None,
        bonus: Optional[float] = None
    ) -> 'Employee':
        return cls(
            id=None,
            telegram_id=telegram_id,
            name=name,
            phone=phone,
            role=role,
            date_start_work=date_start_work,
            probation_months=probation_months,
            base_salary=base_salary,
            bonus=bonus,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
