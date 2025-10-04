from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Group:
    id: Optional[int]
    chat_id: str
    name: str
    created_at: datetime

    @classmethod
    def create(cls, chat_id: str, name: str) -> 'Group':
        return cls(
            id=None,
            chat_id=chat_id,
            name=name,
            created_at=datetime.utcnow()
        )
