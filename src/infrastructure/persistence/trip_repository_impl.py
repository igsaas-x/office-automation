from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
from ...domain.entities.trip import Trip
from ...domain.repositories.trip_repository import ITripRepository
from .models import TripModel

class TripRepository(ITripRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, trip: Trip) -> Trip:
        if trip.id:
            # Update existing
            db_trip = self.session.query(TripModel).filter_by(id=trip.id).first()
            db_trip.trip_number = trip.trip_number
        else:
            # Create new
            db_trip = TripModel(
                group_id=trip.group_id,
                vehicle_id=trip.vehicle_id,
                driver_name=trip.driver_name,
                date=trip.date,
                trip_number=trip.trip_number,
                loading_size_cubic_meters=trip.loading_size_cubic_meters,
                created_at=trip.created_at
            )
            self.session.add(db_trip)

        self.session.commit()
        self.session.refresh(db_trip)

        return self._to_entity(db_trip)

    def find_by_id(self, trip_id: int) -> Optional[Trip]:
        db_trip = self.session.query(TripModel).filter_by(id=trip_id).first()
        return self._to_entity(db_trip) if db_trip else None

    def get_max_trip_number_for_date(self, vehicle_id: int, trip_date: date) -> int:
        max_number = self.session.query(func.max(TripModel.trip_number)).filter_by(
            vehicle_id=vehicle_id,
            date=trip_date
        ).scalar()
        return max_number if max_number else 0

    def find_by_vehicle_and_date_range(
        self,
        vehicle_id: int,
        start_date: date,
        end_date: date
    ) -> List[Trip]:
        db_trips = self.session.query(TripModel).filter(
            TripModel.vehicle_id == vehicle_id,
            TripModel.date >= start_date,
            TripModel.date <= end_date
        ).all()
        return [self._to_entity(t) for t in db_trips]

    def count_by_vehicle_and_date(self, vehicle_id: int, trip_date: date) -> int:
        return self.session.query(TripModel).filter_by(
            vehicle_id=vehicle_id,
            date=trip_date
        ).count()

    def find_by_group_and_date(self, group_id: int, trip_date: date) -> List[Trip]:
        db_trips = self.session.query(TripModel).filter_by(
            group_id=group_id,
            date=trip_date
        ).all()
        return [self._to_entity(t) for t in db_trips]

    def find_by_group_and_date_range(
        self,
        group_id: int,
        start_date: date,
        end_date: date
    ) -> List[Trip]:
        db_trips = self.session.query(TripModel).filter(
            TripModel.group_id == group_id,
            TripModel.date >= start_date,
            TripModel.date <= end_date
        ).all()
        return [self._to_entity(t) for t in db_trips]

    def has_trips_for_vehicle(self, vehicle_id: int) -> bool:
        return self.session.query(TripModel.id).filter_by(vehicle_id=vehicle_id).first() is not None

    def has_trips_for_driver(self, driver_id: int) -> bool:
        return self.session.query(TripModel.id).filter_by(driver_id=driver_id).first() is not None

    def _to_entity(self, model: TripModel) -> Trip:
        return Trip(
            id=model.id,
            group_id=model.group_id,
            vehicle_id=model.vehicle_id,
            driver_name=model.driver_name,
            date=model.date,
            trip_number=model.trip_number,
            loading_size_cubic_meters=model.loading_size_cubic_meters,
            created_at=model.created_at
        )
