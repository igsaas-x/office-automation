from typing import List
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ...domain.entities.check_in import CheckIn
from ...domain.value_objects.location import Location
from ...domain.repositories.check_in_repository import ICheckInRepository
from .models import CheckInModel

class CheckInRepository(ICheckInRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, check_in: CheckIn) -> CheckIn:
        db_check_in = CheckInModel(
            employee_id=check_in.employee_id,
            group_id=check_in.group_id,
            latitude=check_in.location.latitude,
            longitude=check_in.location.longitude,
            photo_url=check_in.photo_url,
            timestamp=check_in.timestamp
        )
        self.session.add(db_check_in)
        self.session.commit()
        self.session.refresh(db_check_in)

        return self._to_entity(db_check_in)

    def find_by_employee_id(self, employee_id: int) -> List[CheckIn]:
        db_check_ins = self.session.query(CheckInModel).filter_by(
            employee_id=employee_id
        ).all()
        return [self._to_entity(db_check_in) for db_check_in in db_check_ins]

    def find_by_group_and_date(self, group_id: int, check_date: date) -> List[CheckIn]:
        """Find all check-ins for a group on a specific date"""
        # Convert date to datetime range (start and end of day)
        start_datetime = datetime.combine(check_date, datetime.min.time())
        end_datetime = datetime.combine(check_date, datetime.max.time())

        db_check_ins = self.session.query(CheckInModel).filter(
            and_(
                CheckInModel.group_id == group_id,
                CheckInModel.timestamp >= start_datetime,
                CheckInModel.timestamp <= end_datetime
            )
        ).order_by(CheckInModel.timestamp.desc()).all()

        return [self._to_entity(db_check_in) for db_check_in in db_check_ins]

    def find_by_group_and_date_range(self, group_id: int, start_date: date, end_date: date) -> List[CheckIn]:
        """Find all check-ins for a group within a date range"""
        # Convert dates to datetime range
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        db_check_ins = self.session.query(CheckInModel).filter(
            and_(
                CheckInModel.group_id == group_id,
                CheckInModel.timestamp >= start_datetime,
                CheckInModel.timestamp <= end_datetime
            )
        ).order_by(CheckInModel.timestamp.desc()).all()

        return [self._to_entity(db_check_in) for db_check_in in db_check_ins]

    def _to_entity(self, model: CheckInModel) -> CheckIn:
        return CheckIn(
            id=model.id,
            employee_id=model.employee_id,
            group_id=model.group_id,
            location=Location(
                latitude=model.latitude,
                longitude=model.longitude
            ),
            timestamp=model.timestamp,
            photo_url=model.photo_url
        )
