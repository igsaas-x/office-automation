from typing import List
from sqlalchemy.orm import Session
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
