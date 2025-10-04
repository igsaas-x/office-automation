from typing import Optional
from ...domain.repositories.employee_repository import IEmployeeRepository
from ..dto.employee_dto import EmployeeResponse

class GetEmployeeUseCase:
    def __init__(self, employee_repository: IEmployeeRepository):
        self.employee_repository = employee_repository

    def execute_by_telegram_id(self, telegram_id: str) -> Optional[EmployeeResponse]:
        employee = self.employee_repository.find_by_telegram_id(telegram_id)
        if not employee:
            return None

        return EmployeeResponse(
            id=employee.id,
            telegram_id=employee.telegram_id,
            name=employee.name
        )

    def execute_by_name(self, name: str) -> Optional[EmployeeResponse]:
        employee = self.employee_repository.find_by_name(name)
        if not employee:
            return None

        return EmployeeResponse(
            id=employee.id,
            telegram_id=employee.telegram_id,
            name=employee.name
        )
