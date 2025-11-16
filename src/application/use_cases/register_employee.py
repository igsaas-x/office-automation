from typing import Optional
from datetime import datetime
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

        # Parse date_start_work if provided
        date_start_work = None
        if request.date_start_work:
            try:
                date_start_work = datetime.fromisoformat(request.date_start_work.replace('Z', '+00:00'))
            except ValueError:
                # Try alternative format
                try:
                    date_start_work = datetime.strptime(request.date_start_work, '%Y-%m-%d')
                except ValueError:
                    raise ValueError("Invalid date format for date_start_work. Use ISO format or YYYY-MM-DD")

        # Create new employee
        employee = Employee.create(
            telegram_id=request.telegram_id,
            name=request.name,
            phone=request.phone,
            role=request.role,
            date_start_work=date_start_work,
            probation_months=request.probation_months,
            base_salary=request.base_salary,
            bonus=request.bonus
        )

        # Save to repository
        saved_employee = self.employee_repository.save(employee)

        return EmployeeResponse(
            id=saved_employee.id,
            telegram_id=saved_employee.telegram_id,
            name=saved_employee.name,
            phone=saved_employee.phone,
            role=saved_employee.role,
            date_start_work=saved_employee.date_start_work.isoformat() if saved_employee.date_start_work else None,
            probation_months=saved_employee.probation_months,
            base_salary=saved_employee.base_salary,
            bonus=saved_employee.bonus,
            created_at=saved_employee.created_at.isoformat() if saved_employee.created_at else None
        )
