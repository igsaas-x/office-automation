from typing import Optional, List
from sqlalchemy.orm import Session
from ...domain.entities.driver import Driver
from ...domain.repositories.driver_repository import IDriverRepository
from .models import DriverModel

class DriverRepository(IDriverRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, driver: Driver) -> Driver:
        if driver.id:
            # Update existing
            db_driver = self.session.query(DriverModel).filter_by(id=driver.id).first()
            db_driver.name = driver.name
            db_driver.phone = driver.phone
            db_driver.role = driver.role
            db_driver.assigned_vehicle_id = driver.assigned_vehicle_id
        else:
            # Create new
            db_driver = DriverModel(
                group_id=driver.group_id,
                name=driver.name,
                phone=driver.phone,
                role=driver.role,
                assigned_vehicle_id=driver.assigned_vehicle_id,
                created_at=driver.created_at
            )
            self.session.add(db_driver)

        self.session.commit()
        self.session.refresh(db_driver)

        return self._to_entity(db_driver)

    def find_by_id(self, driver_id: int) -> Optional[Driver]:
        db_driver = self.session.query(DriverModel).filter_by(id=driver_id).first()
        return self._to_entity(db_driver) if db_driver else None

    def find_by_group_id(self, group_id: int) -> List[Driver]:
        db_drivers = self.session.query(DriverModel).filter_by(group_id=group_id).all()
        return [self._to_entity(d) for d in db_drivers]

    def find_by_phone(self, group_id: int, phone: str) -> Optional[Driver]:
        db_driver = self.session.query(DriverModel).filter_by(
            group_id=group_id,
            phone=phone
        ).first()
        return self._to_entity(db_driver) if db_driver else None

    def delete(self, driver_id: int) -> bool:
        db_driver = self.session.query(DriverModel).filter_by(id=driver_id).first()
        if not db_driver:
            return False

        try:
            self.session.delete(db_driver)
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            raise

    def _to_entity(self, model: DriverModel) -> Driver:
        return Driver(
            id=model.id,
            group_id=model.group_id,
            name=model.name,
            phone=model.phone,
            role=model.role,
            assigned_vehicle_id=model.assigned_vehicle_id,
            created_at=model.created_at
        )
