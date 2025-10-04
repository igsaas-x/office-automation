from abc import ABC, abstractmethod
from typing import List
from ..entities.salary_advance import SalaryAdvance

class ISalaryAdvanceRepository(ABC):
    @abstractmethod
    def save(self, salary_advance: SalaryAdvance) -> SalaryAdvance:
        pass

    @abstractmethod
    def find_by_employee_id(self, employee_id: int) -> List[SalaryAdvance]:
        pass
