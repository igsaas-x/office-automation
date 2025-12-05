from ...domain.entities.vehicle import Vehicle
from ...domain.repositories.vehicle_repository import IVehicleRepository
from ..dto.vehicle_dto import RegisterVehicleRequest, VehicleResponse

class RegisterVehicleUseCase:
    def __init__(self, vehicle_repository: IVehicleRepository):
        self.vehicle_repository = vehicle_repository

    def execute(self, request: RegisterVehicleRequest) -> VehicleResponse:
        # Check if vehicle with same license plate already exists in this group
        existing_vehicle = self.vehicle_repository.find_by_license_plate(
            request.group_id,
            request.license_plate
        )
        if existing_vehicle:
            raise ValueError(f"Vehicle with license plate '{request.license_plate}' already exists in this group")

        # Validate vehicle type
        valid_types = ['TRUCK', 'VAN', 'MOTORCYCLE', 'CAR']
        if request.vehicle_type.upper() not in valid_types:
            raise ValueError(f"Invalid vehicle type. Must be one of: {', '.join(valid_types)}")

        # Create new vehicle
        vehicle = Vehicle.create(
            group_id=request.group_id,
            license_plate=request.license_plate,
            vehicle_type=request.vehicle_type.upper(),
            driver_name=request.driver_name
        )

        # Save to repository
        saved_vehicle = self.vehicle_repository.save(vehicle)

        return VehicleResponse(
            id=saved_vehicle.id,
            group_id=saved_vehicle.group_id,
            license_plate=saved_vehicle.license_plate,
            vehicle_type=saved_vehicle.vehicle_type,
            driver_name=saved_vehicle.driver_name,
            created_at=saved_vehicle.created_at.isoformat()
        )
