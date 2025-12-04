from datetime import date
from ...domain.entities.fuel_record import FuelRecord
from ...domain.repositories.fuel_record_repository import IFuelRecordRepository
from ...domain.repositories.vehicle_repository import IVehicleRepository
from ..dto.fuel_dto import RecordFuelRequest, FuelResponse

class RecordFuelUseCase:
    def __init__(
        self,
        fuel_record_repository: IFuelRecordRepository,
        vehicle_repository: IVehicleRepository
    ):
        self.fuel_record_repository = fuel_record_repository
        self.vehicle_repository = vehicle_repository

    def execute(self, request: RecordFuelRequest) -> FuelResponse:
        # Validate vehicle exists and belongs to group
        vehicle = self.vehicle_repository.find_by_id(request.vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle with ID {request.vehicle_id} not found")
        if vehicle.group_id != request.group_id:
            raise ValueError("Vehicle does not belong to this group")

        # Validate fuel data
        if request.liters <= 0:
            raise ValueError("Liters must be greater than 0")
        if request.cost <= 0:
            raise ValueError("Cost must be greater than 0")

        # Get today's date
        today = date.today()

        # Create new fuel record
        fuel_record = FuelRecord.create(
            group_id=request.group_id,
            vehicle_id=request.vehicle_id,
            fuel_date=today,
            liters=request.liters,
            cost=request.cost,
            receipt_photo_url=request.receipt_photo_url
        )

        # Save to repository
        saved_fuel_record = self.fuel_record_repository.save(fuel_record)

        return FuelResponse(
            id=saved_fuel_record.id,
            group_id=saved_fuel_record.group_id,
            vehicle_id=saved_fuel_record.vehicle_id,
            date=saved_fuel_record.date.isoformat(),
            liters=saved_fuel_record.liters,
            cost=saved_fuel_record.cost,
            receipt_photo_url=saved_fuel_record.receipt_photo_url,
            created_at=saved_fuel_record.created_at.isoformat(),
            vehicle_license_plate=vehicle.license_plate
        )
