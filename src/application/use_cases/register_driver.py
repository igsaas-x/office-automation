from ...domain.entities.driver import Driver
from ...domain.repositories.driver_repository import IDriverRepository
from ...domain.repositories.vehicle_repository import IVehicleRepository
from ..dto.driver_dto import RegisterDriverRequest, DriverResponse

class RegisterDriverUseCase:
    def __init__(
        self,
        driver_repository: IDriverRepository,
        vehicle_repository: IVehicleRepository
    ):
        self.driver_repository = driver_repository
        self.vehicle_repository = vehicle_repository

    def execute(self, request: RegisterDriverRequest) -> DriverResponse:
        # Check if driver with same phone already exists in this group
        existing_driver = self.driver_repository.find_by_phone(
            request.group_id,
            request.phone
        )
        if existing_driver:
            raise ValueError(f"Driver with phone '{request.phone}' already exists in this group")

        # Validate assigned vehicle if provided
        if request.assigned_vehicle_id:
            vehicle = self.vehicle_repository.find_by_id(request.assigned_vehicle_id)
            if not vehicle:
                raise ValueError(f"Vehicle with ID {request.assigned_vehicle_id} not found")
            if vehicle.group_id != request.group_id:
                raise ValueError("Vehicle does not belong to this group")

        # Create new driver
        driver = Driver.create(
            group_id=request.group_id,
            name=request.name,
            phone=request.phone,
            assigned_vehicle_id=request.assigned_vehicle_id,
            role=request.role
        )

        # Save to repository
        saved_driver = self.driver_repository.save(driver)

        return DriverResponse(
            id=saved_driver.id,
            group_id=saved_driver.group_id,
            name=saved_driver.name,
            phone=saved_driver.phone,
            role=saved_driver.role,
            assigned_vehicle_id=saved_driver.assigned_vehicle_id,
            created_at=saved_driver.created_at.isoformat()
        )
