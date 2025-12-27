from ...domain.entities.employee_group import EmployeeGroup
from ...domain.repositories.employee_group_repository import IEmployeeGroupRepository
from ...domain.repositories.employee_repository import IEmployeeRepository
from ...domain.repositories.group_repository import IGroupRepository

class AddEmployeeToGroupUseCase:
    def __init__(
        self,
        employee_group_repository: IEmployeeGroupRepository,
        employee_repository: IEmployeeRepository,
        group_repository: IGroupRepository
    ):
        self.employee_group_repository = employee_group_repository
        self.employee_repository = employee_repository
        self.group_repository = group_repository

    def execute(self, employee_id: int, group_id: int) -> EmployeeGroup:
        # Verify employee exists
        employee = self.employee_repository.find_by_id(employee_id)
        if not employee:
            raise ValueError("Employee not found")

        # Verify group exists
        group = self.group_repository.find_by_id(group_id)
        if not group:
            raise ValueError("Group not found")

        # Return existing association if present
        if self.employee_group_repository.exists(employee_id, group_id):
            existing = self.employee_group_repository.find_by_employee_and_group(
                employee_id,
                group_id
            )
            if existing:
                return existing

        # Create association
        employee_group = EmployeeGroup.create(
            employee_id=employee_id,
            group_id=group_id
        )

        return self.employee_group_repository.save(employee_group)
