from abc import ABC, abstractmethod
from typing import List
from ..entities.allowance import Allowance

class IAllowanceRepository(ABC):
    @abstractmethod
    def save(self, allowance: Allowance) -> Allowance:
        pass

    @abstractmethod
    def find_by_employee_id(self, employee_id: int) -> List[Allowance]:
        pass
