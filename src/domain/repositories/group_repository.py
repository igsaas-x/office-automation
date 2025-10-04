from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.group import Group

class IGroupRepository(ABC):
    @abstractmethod
    def save(self, group: Group) -> Group:
        pass

    @abstractmethod
    def find_by_id(self, group_id: int) -> Optional[Group]:
        pass

    @abstractmethod
    def find_by_chat_id(self, chat_id: str) -> Optional[Group]:
        pass

    @abstractmethod
    def find_all(self) -> List[Group]:
        pass
