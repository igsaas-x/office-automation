from typing import List
from decimal import Decimal
from sqlalchemy.orm import Session
from ...domain.entities.salary_advance import SalaryAdvance
from ...domain.value_objects.money import Money
from ...domain.repositories.salary_advance_repository import ISalaryAdvanceRepository
from .models import SalaryAdvanceModel

class SalaryAdvanceRepository(ISalaryAdvanceRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, salary_advance: SalaryAdvance) -> SalaryAdvance:
        db_advance = SalaryAdvanceModel(
            employee_id=salary_advance.employee_id,
            amount=str(salary_advance.amount.amount),
            note=salary_advance.note,
            created_by=salary_advance.created_by,
            timestamp=salary_advance.timestamp
        )
        self.session.add(db_advance)
        self.session.commit()
        self.session.refresh(db_advance)

        return self._to_entity(db_advance)

    def find_by_employee_id(self, employee_id: int) -> List[SalaryAdvance]:
        db_advances = self.session.query(SalaryAdvanceModel).filter_by(
            employee_id=employee_id
        ).all()
        return [self._to_entity(db_advance) for db_advance in db_advances]

    def _to_entity(self, model: SalaryAdvanceModel) -> SalaryAdvance:
        return SalaryAdvance(
            id=model.id,
            employee_id=model.employee_id,
            amount=Money(Decimal(model.amount)),
            note=model.note,
            created_by=model.created_by,
            timestamp=model.timestamp
        )
