from typing import List
from sqlalchemy.orm import Session
from ...domain.entities.allowance import Allowance
from ...domain.repositories.allowance_repository import IAllowanceRepository
from .models import AllowanceModel

class AllowanceRepository(IAllowanceRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, allowance: Allowance) -> Allowance:
        db_allowance = AllowanceModel(
            employee_id=allowance.employee_id,
            amount=allowance.amount,
            allowance_type=allowance.allowance_type,
            note=allowance.note,
            created_by=allowance.created_by,
            timestamp=allowance.timestamp
        )
        self.session.add(db_allowance)
        self.session.commit()
        self.session.refresh(db_allowance)

        return self._to_entity(db_allowance)

    def find_by_employee_id(self, employee_id: int) -> List[Allowance]:
        db_allowances = self.session.query(AllowanceModel).filter_by(
            employee_id=employee_id
        ).all()
        return [self._to_entity(db_allowance) for db_allowance in db_allowances]

    def _to_entity(self, model: AllowanceModel) -> Allowance:
        return Allowance(
            id=model.id,
            employee_id=model.employee_id,
            amount=model.amount,
            allowance_type=model.allowance_type,
            note=model.note,
            created_by=model.created_by,
            timestamp=model.timestamp
        )
