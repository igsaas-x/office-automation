from ...domain.entities.check_in import CheckIn
from ...domain.value_objects.location import Location
from ...domain.repositories.check_in_repository import ICheckInRepository
from ...domain.repositories.employee_repository import IEmployeeRepository
from ..dto.check_in_dto import CheckInRequest, CheckInResponse

class RecordCheckInUseCase:
    def __init__(
        self,
        check_in_repository: ICheckInRepository,
        employee_repository: IEmployeeRepository
    ):
        self.check_in_repository = check_in_repository
        self.employee_repository = employee_repository

    def execute(self, request: CheckInRequest) -> CheckInResponse:
        # Verify employee exists
        employee = self.employee_repository.find_by_id(request.employee_id)
        if not employee:
            raise ValueError("Employee not found")

        # Create location value object
        location = Location(
            latitude=request.latitude,
            longitude=request.longitude
        )

        # Create check-in
        check_in = CheckIn.create(
            employee_id=request.employee_id,
            location=location
        )

        # Save check-in
        saved_check_in = self.check_in_repository.save(check_in)

        return CheckInResponse(
            success=True,
            message="Check-in recorded successfully",
            timestamp=saved_check_in.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            location=f"{location.latitude}, {location.longitude}"
        )
