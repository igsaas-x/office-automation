from abc import ABC, abstractmethod
from typing import Optional
from ..entities.employee import Employee

class IEmployeeRepository(ABC):
    @abstractmethod
    def save(self, employee: Employee) -> Employee:
        pass

    @abstractmethod
    def find_by_id(self, employee_id: int) -> Optional[Employee]:
        pass

    @abstractmethod
    def find_by_telegram_id(self, telegram_id: str) -> Optional[Employee]:
        pass

    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Employee]:
        pass
