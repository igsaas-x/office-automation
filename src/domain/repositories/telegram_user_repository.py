from abc import ABC, abstractmethod
from typing import Optional
from ..entities.telegram_user import TelegramUser

class ITelegramUserRepository(ABC):
    @abstractmethod
    def save(self, user: TelegramUser) -> TelegramUser:
        pass

    @abstractmethod
    def find_by_telegram_id(self, telegram_id: str) -> Optional[TelegramUser]:
        pass

    @abstractmethod
    def find_by_id(self, user_id: int) -> Optional[TelegramUser]:
        pass
