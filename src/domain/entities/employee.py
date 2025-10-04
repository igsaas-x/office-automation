from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Employee:
    id: Optional[int]
    telegram_id: str
    name: str
    created_at: datetime

    @classmethod
    def create(cls, telegram_id: str, name: str) -> 'Employee':
        return cls(
            id=None,
            telegram_id=telegram_id,
            name=name,
            created_at=datetime.utcnow()
        )
