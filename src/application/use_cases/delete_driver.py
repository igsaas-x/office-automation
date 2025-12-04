from ...domain.repositories.driver_repository import IDriverRepository
from ...domain.repositories.trip_repository import ITripRepository
from ..dto.driver_dto import DeleteDriverResponse


class DeleteDriverUseCase:
    def __init__(
        self,
        driver_repository: IDriverRepository,
        trip_repository: ITripRepository
    ):
        self.driver_repository = driver_repository
        self.trip_repository = trip_repository

    def execute(self, group_id: int, driver_id: int) -> DeleteDriverResponse:
        driver = self.driver_repository.find_by_id(driver_id)
        if not driver or driver.group_id != group_id:
            raise ValueError("Driver not found for this group")

        if self.trip_repository.has_trips_for_driver(driver_id):
            raise ValueError("Cannot delete driver with existing trip records")

        deleted = self.driver_repository.delete(driver_id)
        if not deleted:
            raise ValueError("Driver not found")

        return DeleteDriverResponse(
            id=driver.id,
            name=driver.name,
            phone=driver.phone
        )
