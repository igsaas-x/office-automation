from ...domain.entities.salary_advance import SalaryAdvance
from ...domain.value_objects.money import Money
from ...domain.repositories.salary_advance_repository import ISalaryAdvanceRepository
from ...domain.repositories.employee_repository import IEmployeeRepository
from ..dto.salary_advance_dto import SalaryAdvanceRequest, SalaryAdvanceResponse

class RecordSalaryAdvanceUseCase:
    def __init__(
        self,
        salary_advance_repository: ISalaryAdvanceRepository,
        employee_repository: IEmployeeRepository
    ):
        self.salary_advance_repository = salary_advance_repository
        self.employee_repository = employee_repository

    def execute(self, request: SalaryAdvanceRequest) -> SalaryAdvanceResponse:
        # Find employee by name
        employee = self.employee_repository.find_by_name(request.employee_name)
        if not employee:
            raise ValueError(f"Employee '{request.employee_name}' not found")

        # Create money value object
        money = Money.from_float(request.amount)

        # Create salary advance
        salary_advance = SalaryAdvance.create(
            employee_id=employee.id,
            amount=money,
            created_by=request.created_by,
            note=request.note
        )

        # Save salary advance
        saved_advance = self.salary_advance_repository.save(salary_advance)

        return SalaryAdvanceResponse(
            success=True,
            message="Salary advance recorded successfully",
            employee_name=employee.name,
            amount=str(saved_advance.amount),
            timestamp=saved_advance.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        )
