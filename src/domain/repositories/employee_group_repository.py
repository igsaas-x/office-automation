from abc import ABC, abstractmethod
from typing import List
from ..entities.employee_group import EmployeeGroup

class IEmployeeGroupRepository(ABC):
    @abstractmethod
    def save(self, employee_group: EmployeeGroup) -> EmployeeGroup:
        pass

    @abstractmethod
    def find_by_employee_id(self, employee_id: int) -> List[EmployeeGroup]:
        pass

    @abstractmethod
    def find_by_group_id(self, group_id: int) -> List[EmployeeGroup]:
        pass

    @abstractmethod
    def exists(self, employee_id: int, group_id: int) -> bool:
        pass
