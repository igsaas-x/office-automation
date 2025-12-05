from datetime import date
from ...domain.entities.trip import Trip
from ...domain.repositories.trip_repository import ITripRepository
from ...domain.repositories.vehicle_repository import IVehicleRepository
from ..dto.trip_dto import RecordTripRequest, TripResponse

class RecordTripUseCase:
    def __init__(
        self,
        trip_repository: ITripRepository,
        vehicle_repository: IVehicleRepository
    ):
        self.trip_repository = trip_repository
        self.vehicle_repository = vehicle_repository

    def execute(self, request: RecordTripRequest) -> TripResponse:
        # Validate vehicle exists and belongs to group
        vehicle = self.vehicle_repository.find_by_id(request.vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle with ID {request.vehicle_id} not found")
        if vehicle.group_id != request.group_id:
            raise ValueError("Vehicle does not belong to this group")

        # Get today's date
        today = date.today()

        # Get next trip number for this vehicle today (auto-increment)
        max_trip_number = self.trip_repository.get_max_trip_number_for_date(
            request.vehicle_id,
            today
        )
        next_trip_number = max_trip_number + 1

        # Create new trip (snapshot driver name from vehicle)
        trip = Trip.create(
            group_id=request.group_id,
            vehicle_id=request.vehicle_id,
            driver_name=vehicle.driver_name,
            trip_date=today,
            trip_number=next_trip_number,
            loading_size_cubic_meters=request.loading_size_cubic_meters
        )

        # Save to repository
        saved_trip = self.trip_repository.save(trip)

        # Get total trips for today for this vehicle
        total_trips_today = self.trip_repository.count_by_vehicle_and_date(
            request.vehicle_id,
            today
        )

        return TripResponse(
            id=saved_trip.id,
            group_id=saved_trip.group_id,
            vehicle_id=saved_trip.vehicle_id,
            driver_name=saved_trip.driver_name,
            date=saved_trip.date.isoformat(),
            trip_number=saved_trip.trip_number,
            loading_size_cubic_meters=saved_trip.loading_size_cubic_meters,
            created_at=saved_trip.created_at.isoformat(),
            vehicle_license_plate=vehicle.license_plate
        )
