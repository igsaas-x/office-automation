from ...domain.entities.allowance import Allowance
from ...domain.repositories.allowance_repository import IAllowanceRepository
from ...domain.repositories.employee_repository import IEmployeeRepository
from ..dto.allowance_dto import RecordAllowanceRequest, AllowanceResponse

class RecordAllowanceUseCase:
    def __init__(
        self,
        allowance_repository: IAllowanceRepository,
        employee_repository: IEmployeeRepository
    ):
        self.allowance_repository = allowance_repository
        self.employee_repository = employee_repository

    def execute(self, request: RecordAllowanceRequest) -> AllowanceResponse:
        # Verify employee exists
        employee = self.employee_repository.find_by_id(request.employee_id)
        if not employee:
            raise ValueError(f"Employee with ID {request.employee_id} not found")

        # Create allowance
        allowance = Allowance.create(
            employee_id=request.employee_id,
            amount=request.amount,
            allowance_type=request.allowance_type,
            created_by=request.created_by,
            note=request.note
        )

        # Save allowance
        saved_allowance = self.allowance_repository.save(allowance)

        return AllowanceResponse(
            id=saved_allowance.id,
            employee_id=saved_allowance.employee_id,
            amount=saved_allowance.amount,
            allowance_type=saved_allowance.allowance_type,
            note=saved_allowance.note,
            created_by=saved_allowance.created_by,
            timestamp=saved_allowance.timestamp.isoformat()
        )
