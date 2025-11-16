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
            db_employee.phone = employee.phone
            db_employee.role = employee.role
            db_employee.date_start_work = employee.date_start_work
            db_employee.probation_months = employee.probation_months
            db_employee.base_salary = employee.base_salary
            db_employee.bonus = employee.bonus
        else:
            # Create new
            db_employee = EmployeeModel(
                telegram_id=employee.telegram_id,
                name=employee.name,
                phone=employee.phone,
                role=employee.role,
                date_start_work=employee.date_start_work,
                probation_months=employee.probation_months,
                base_salary=employee.base_salary,
                bonus=employee.bonus,
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
            phone=model.phone,
            role=model.role,
            date_start_work=model.date_start_work,
            probation_months=model.probation_months,
            base_salary=model.base_salary,
            bonus=model.bonus,
            created_at=model.created_at
        )
