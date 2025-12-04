from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.driver import Driver

class IDriverRepository(ABC):
    @abstractmethod
    def save(self, driver: Driver) -> Driver:
        pass

    @abstractmethod
    def find_by_id(self, driver_id: int) -> Optional[Driver]:
        pass

    @abstractmethod
    def find_by_group_id(self, group_id: int) -> List[Driver]:
        pass

    @abstractmethod
    def find_by_phone(self, group_id: int, phone: str) -> Optional[Driver]:
        pass
