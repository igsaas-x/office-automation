from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session
from ...domain.entities.fuel_record import FuelRecord
from ...domain.repositories.fuel_record_repository import IFuelRecordRepository
from .models import FuelRecordModel

class FuelRecordRepository(IFuelRecordRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, fuel_record: FuelRecord) -> FuelRecord:
        if fuel_record.id:
            # Update existing
            db_fuel = self.session.query(FuelRecordModel).filter_by(id=fuel_record.id).first()
            db_fuel.liters = fuel_record.liters
            db_fuel.cost = fuel_record.cost
            db_fuel.receipt_photo_url = fuel_record.receipt_photo_url
        else:
            # Create new
            db_fuel = FuelRecordModel(
                group_id=fuel_record.group_id,
                vehicle_id=fuel_record.vehicle_id,
                date=fuel_record.date,
                liters=fuel_record.liters,
                cost=fuel_record.cost,
                receipt_photo_url=fuel_record.receipt_photo_url,
                created_at=fuel_record.created_at
            )
            self.session.add(db_fuel)

        self.session.commit()
        self.session.refresh(db_fuel)

        return self._to_entity(db_fuel)

    def find_by_id(self, fuel_record_id: int) -> Optional[FuelRecord]:
        db_fuel = self.session.query(FuelRecordModel).filter_by(id=fuel_record_id).first()
        return self._to_entity(db_fuel) if db_fuel else None

    def find_by_vehicle_and_date_range(
        self,
        vehicle_id: int,
        start_date: date,
        end_date: date
    ) -> List[FuelRecord]:
        db_fuels = self.session.query(FuelRecordModel).filter(
            FuelRecordModel.vehicle_id == vehicle_id,
            FuelRecordModel.date >= start_date,
            FuelRecordModel.date <= end_date
        ).all()
        return [self._to_entity(f) for f in db_fuels]

    def find_by_group_and_date(self, group_id: int, fuel_date: date) -> List[FuelRecord]:
        db_fuels = self.session.query(FuelRecordModel).filter_by(
            group_id=group_id,
            date=fuel_date
        ).all()
        return [self._to_entity(f) for f in db_fuels]

    def find_by_group_and_date_range(
        self,
        group_id: int,
        start_date: date,
        end_date: date
    ) -> List[FuelRecord]:
        db_fuels = self.session.query(FuelRecordModel).filter(
            FuelRecordModel.group_id == group_id,
            FuelRecordModel.date >= start_date,
            FuelRecordModel.date <= end_date
        ).all()
        return [self._to_entity(f) for f in db_fuels]

    def has_records_for_vehicle(self, vehicle_id: int) -> bool:
        return self.session.query(FuelRecordModel.id).filter_by(vehicle_id=vehicle_id).first() is not None

    def _to_entity(self, model: FuelRecordModel) -> FuelRecord:
        return FuelRecord(
            id=model.id,
            group_id=model.group_id,
            vehicle_id=model.vehicle_id,
            date=model.date,
            liters=model.liters,
            cost=model.cost,
            receipt_photo_url=model.receipt_photo_url,
            created_at=model.created_at
        )
