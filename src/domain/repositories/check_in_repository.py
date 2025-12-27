from abc import ABC, abstractmethod
from typing import List
from datetime import date
from ..entities.check_in import CheckIn

class ICheckInRepository(ABC):
    @abstractmethod
    def save(self, check_in: CheckIn) -> CheckIn:
        pass

    @abstractmethod
    def find_by_employee_id(self, employee_id: int) -> List[CheckIn]:
        pass

    @abstractmethod
    def find_by_group_and_date(self, group_id: int, check_date: date) -> List[CheckIn]:
        """Find all check-ins for a group on a specific date"""
        pass

    @abstractmethod
    def find_by_group_and_date_range(self, group_id: int, start_date: date, end_date: date) -> List[CheckIn]:
        """Find all check-ins for a group within a date range"""
        pass
