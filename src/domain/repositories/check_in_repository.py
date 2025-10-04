from abc import ABC, abstractmethod
from typing import List
from ..entities.check_in import CheckIn

class ICheckInRepository(ABC):
    @abstractmethod
    def save(self, check_in: CheckIn) -> CheckIn:
        pass

    @abstractmethod
    def find_by_employee_id(self, employee_id: int) -> List[CheckIn]:
        pass
