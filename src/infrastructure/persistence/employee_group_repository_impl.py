from typing import List, Optional
from sqlalchemy.orm import Session
from ...domain.entities.employee_group import EmployeeGroup
from ...domain.repositories.employee_group_repository import IEmployeeGroupRepository
from .models import EmployeeGroupModel

class EmployeeGroupRepository(IEmployeeGroupRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, employee_group: EmployeeGroup) -> EmployeeGroup:
        db_employee_group = EmployeeGroupModel(
            employee_id=employee_group.employee_id,
            group_id=employee_group.group_id,
            joined_at=employee_group.joined_at
        )
        self.session.add(db_employee_group)
        self.session.commit()
        self.session.refresh(db_employee_group)

        return self._to_entity(db_employee_group)

    def find_by_employee_id(self, employee_id: int) -> List[EmployeeGroup]:
        db_employee_groups = self.session.query(EmployeeGroupModel).filter_by(
            employee_id=employee_id
        ).all()
        return [self._to_entity(db_eg) for db_eg in db_employee_groups]

    def find_by_group_id(self, group_id: int) -> List[EmployeeGroup]:
        db_employee_groups = self.session.query(EmployeeGroupModel).filter_by(
            group_id=group_id
        ).all()
        return [self._to_entity(db_eg) for db_eg in db_employee_groups]

    def exists(self, employee_id: int, group_id: int) -> bool:
        return self.session.query(EmployeeGroupModel).filter_by(
            employee_id=employee_id,
            group_id=group_id
        ).first() is not None

    def find_by_employee_and_group(self, employee_id: int, group_id: int) -> Optional[EmployeeGroup]:
        db_employee_group = self.session.query(EmployeeGroupModel).filter_by(
            employee_id=employee_id,
            group_id=group_id
        ).first()
        return self._to_entity(db_employee_group) if db_employee_group else None

    def _to_entity(self, model: EmployeeGroupModel) -> EmployeeGroup:
        return EmployeeGroup(
            id=model.id,
            employee_id=model.employee_id,
            group_id=model.group_id,
            joined_at=model.joined_at
        )
