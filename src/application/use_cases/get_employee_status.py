from dataclasses import dataclass
from typing import List, Optional
from ...domain.repositories.employee_repository import IEmployeeRepository
from ...domain.repositories.salary_advance_repository import ISalaryAdvanceRepository
from ...domain.repositories.allowance_repository import IAllowanceRepository

@dataclass
class SalaryAdvanceSummary:
    id: int
    amount: str
    note: Optional[str]
    created_by: str
    timestamp: str

@dataclass
class AllowanceSummary:
    id: int
    amount: float
    allowance_type: str
    note: Optional[str]
    created_by: str
    timestamp: str

@dataclass
class EmployeeStatusResponse:
    id: int
    telegram_id: str
    name: str
    phone: Optional[str]
    role: Optional[str]
    date_start_work: Optional[str]
    probation_months: Optional[int]
    base_salary: Optional[float]
    bonus: Optional[float]
    created_at: str
    salary_advances: List[SalaryAdvanceSummary]
    allowances: List[AllowanceSummary]
    total_salary_advances: float
    total_allowances: float

class GetEmployeeStatusUseCase:
    def __init__(
        self,
        employee_repository: IEmployeeRepository,
        salary_advance_repository: ISalaryAdvanceRepository,
        allowance_repository: IAllowanceRepository
    ):
        self.employee_repository = employee_repository
        self.salary_advance_repository = salary_advance_repository
        self.allowance_repository = allowance_repository

    def execute_by_id(self, employee_id: int) -> EmployeeStatusResponse:
        # Get employee
        employee = self.employee_repository.find_by_id(employee_id)
        if not employee:
            raise ValueError(f"Employee with ID {employee_id} not found")

        return self._build_response(employee)

    def execute_by_telegram_id(self, telegram_id: str) -> EmployeeStatusResponse:
        # Get employee
        employee = self.employee_repository.find_by_telegram_id(telegram_id)
        if not employee:
            raise ValueError(f"Employee with Telegram ID {telegram_id} not found")

        return self._build_response(employee)

    def _build_response(self, employee) -> EmployeeStatusResponse:
        # Get salary advances
        salary_advances = self.salary_advance_repository.find_by_employee_id(employee.id)
        salary_advance_summaries = [
            SalaryAdvanceSummary(
                id=adv.id,
                amount=str(adv.amount),
                note=adv.note,
                created_by=adv.created_by,
                timestamp=adv.timestamp.isoformat()
            )
            for adv in salary_advances
        ]

        # Get allowances
        allowances = self.allowance_repository.find_by_employee_id(employee.id)
        allowance_summaries = [
            AllowanceSummary(
                id=allow.id,
                amount=allow.amount,
                allowance_type=allow.allowance_type,
                note=allow.note,
                created_by=allow.created_by,
                timestamp=allow.timestamp.isoformat()
            )
            for allow in allowances
        ]

        # Calculate totals
        total_salary_advances = sum(float(adv.amount.amount) for adv in salary_advances)
        total_allowances = sum(allow.amount for allow in allowances)

        return EmployeeStatusResponse(
            id=employee.id,
            telegram_id=employee.telegram_id,
            name=employee.name,
            phone=employee.phone,
            role=employee.role,
            date_start_work=employee.date_start_work.isoformat() if employee.date_start_work else None,
            probation_months=employee.probation_months,
            base_salary=employee.base_salary,
            bonus=employee.bonus,
            created_at=employee.created_at.isoformat(),
            salary_advances=salary_advance_summaries,
            allowances=allowance_summaries,
            total_salary_advances=total_salary_advances,
            total_allowances=total_allowances
        )
