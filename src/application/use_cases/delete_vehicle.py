from ...domain.repositories.vehicle_repository import IVehicleRepository
from ...domain.repositories.trip_repository import ITripRepository
from ...domain.repositories.fuel_record_repository import IFuelRecordRepository
from ..dto.vehicle_dto import DeleteVehicleResponse


class DeleteVehicleUseCase:
    def __init__(
        self,
        vehicle_repository: IVehicleRepository,
        trip_repository: ITripRepository,
        fuel_record_repository: IFuelRecordRepository
    ):
        self.vehicle_repository = vehicle_repository
        self.trip_repository = trip_repository
        self.fuel_record_repository = fuel_record_repository

    def execute(self, group_id: int, vehicle_id: int) -> DeleteVehicleResponse:
        vehicle = self.vehicle_repository.find_by_id(vehicle_id)
        if not vehicle or vehicle.group_id != group_id:
            raise ValueError("Vehicle not found for this group")

        # Prevent deletion if operational data exists
        if self.trip_repository.has_trips_for_vehicle(vehicle_id):
            raise ValueError("Cannot delete vehicle with existing trip records")

        if self.fuel_record_repository.has_records_for_vehicle(vehicle_id):
            raise ValueError("Cannot delete vehicle with existing fuel records")

        deleted = self.vehicle_repository.delete(vehicle_id)
        if not deleted:
            raise ValueError("Vehicle not found")

        return DeleteVehicleResponse(
            id=vehicle.id,
            license_plate=vehicle.license_plate
        )
