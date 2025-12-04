from typing import Optional, List
from sqlalchemy.orm import Session
from ...domain.entities.vehicle import Vehicle
from ...domain.repositories.vehicle_repository import IVehicleRepository
from .models import VehicleModel

class VehicleRepository(IVehicleRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, vehicle: Vehicle) -> Vehicle:
        if vehicle.id:
            # Update existing
            db_vehicle = self.session.query(VehicleModel).filter_by(id=vehicle.id).first()
            db_vehicle.license_plate = vehicle.license_plate
            db_vehicle.vehicle_type = vehicle.vehicle_type
        else:
            # Create new
            db_vehicle = VehicleModel(
                group_id=vehicle.group_id,
                license_plate=vehicle.license_plate,
                vehicle_type=vehicle.vehicle_type,
                created_at=vehicle.created_at
            )
            self.session.add(db_vehicle)

        self.session.commit()
        self.session.refresh(db_vehicle)

        return self._to_entity(db_vehicle)

    def find_by_id(self, vehicle_id: int) -> Optional[Vehicle]:
        db_vehicle = self.session.query(VehicleModel).filter_by(id=vehicle_id).first()
        return self._to_entity(db_vehicle) if db_vehicle else None

    def find_by_group_id(self, group_id: int) -> List[Vehicle]:
        db_vehicles = self.session.query(VehicleModel).filter_by(group_id=group_id).all()
        return [self._to_entity(v) for v in db_vehicles]

    def find_by_license_plate(self, group_id: int, license_plate: str) -> Optional[Vehicle]:
        db_vehicle = self.session.query(VehicleModel).filter_by(
            group_id=group_id,
            license_plate=license_plate
        ).first()
        return self._to_entity(db_vehicle) if db_vehicle else None

    def delete(self, vehicle_id: int) -> bool:
        db_vehicle = self.session.query(VehicleModel).filter_by(id=vehicle_id).first()
        if not db_vehicle:
            return False

        try:
            self.session.delete(db_vehicle)
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            raise

    def _to_entity(self, model: VehicleModel) -> Vehicle:
        return Vehicle(
            id=model.id,
            group_id=model.group_id,
            license_plate=model.license_plate,
            vehicle_type=model.vehicle_type,
            created_at=model.created_at
        )
