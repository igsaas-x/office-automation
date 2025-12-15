from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

@dataclass
class TelegramUser:
    id: Optional[int]
    telegram_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        telegram_id: str,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> 'TelegramUser':
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        return cls(
            id=None,
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            created_at=now,
            updated_at=now
        )
