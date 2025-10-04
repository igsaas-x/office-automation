from typing import Optional
from sqlalchemy.orm import Session
from ...domain.entities.employee import Employee
from ...domain.repositories.employee_repository import IEmployeeRepository
from .models import EmployeeModel

class EmployeeRepository(IEmployeeRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, employee: Employee) -> Employee:
        if employee.id:
            # Update existing
            db_employee = self.session.query(EmployeeModel).filter_by(id=employee.id).first()
            db_employee.name = employee.name
            db_employee.telegram_id = employee.telegram_id
        else:
            # Create new
            db_employee = EmployeeModel(
                telegram_id=employee.telegram_id,
                name=employee.name,
                created_at=employee.created_at
            )
            self.session.add(db_employee)

        self.session.commit()
        self.session.refresh(db_employee)

        return self._to_entity(db_employee)

    def find_by_id(self, employee_id: int) -> Optional[Employee]:
        db_employee = self.session.query(EmployeeModel).filter_by(id=employee_id).first()
        return self._to_entity(db_employee) if db_employee else None

    def find_by_telegram_id(self, telegram_id: str) -> Optional[Employee]:
        db_employee = self.session.query(EmployeeModel).filter_by(telegram_id=telegram_id).first()
        return self._to_entity(db_employee) if db_employee else None

    def find_by_name(self, name: str) -> Optional[Employee]:
        db_employee = self.session.query(EmployeeModel).filter(
            EmployeeModel.name.ilike(f"%{name}%")
        ).first()
        return self._to_entity(db_employee) if db_employee else None

    def _to_entity(self, model: EmployeeModel) -> Employee:
        return Employee(
            id=model.id,
            telegram_id=model.telegram_id,
            name=model.name,
            created_at=model.created_at
        )
