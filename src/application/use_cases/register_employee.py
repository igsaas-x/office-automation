from typing import Optional
from ...domain.entities.employee import Employee
from ...domain.repositories.employee_repository import IEmployeeRepository
from ..dto.employee_dto import RegisterEmployeeRequest, EmployeeResponse

class RegisterEmployeeUseCase:
    def __init__(self, employee_repository: IEmployeeRepository):
        self.employee_repository = employee_repository

    def execute(self, request: RegisterEmployeeRequest) -> EmployeeResponse:
        # Check if employee already exists
        existing_employee = self.employee_repository.find_by_telegram_id(request.telegram_id)
        if existing_employee:
            raise ValueError("Employee already registered")

        # Create new employee
        employee = Employee.create(
            telegram_id=request.telegram_id,
            name=request.name
        )

        # Save to repository
        saved_employee = self.employee_repository.save(employee)

        return EmployeeResponse(
            id=saved_employee.id,
            telegram_id=saved_employee.telegram_id,
            name=saved_employee.name
        )
