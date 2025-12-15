from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

@dataclass
class Group:
    id: Optional[int]
    chat_id: str
    name: str
    business_name: Optional[str] = None
    package_level: str = 'free'  # free, basic, premium
    package_updated_at: Optional[datetime] = None
    package_updated_by: Optional[str] = None
    created_by_telegram_id: Optional[str] = None
    created_by_username: Optional[str] = None
    created_by_first_name: Optional[str] = None
    created_by_last_name: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        chat_id: str,
        name: str,
        business_name: Optional[str] = None,
        created_by_telegram_id: Optional[str] = None,
        created_by_username: Optional[str] = None,
        created_by_first_name: Optional[str] = None,
        created_by_last_name: Optional[str] = None
    ) -> 'Group':
        return cls(
            id=None,
            chat_id=chat_id,
            name=name,
            business_name=business_name,
            package_level='free',
            package_updated_at=None,
            package_updated_by=None,
            created_by_telegram_id=created_by_telegram_id,
            created_by_username=created_by_username,
            created_by_first_name=created_by_first_name,
            created_by_last_name=created_by_last_name,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
