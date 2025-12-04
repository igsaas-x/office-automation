from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import date
from ..entities.trip import Trip

class ITripRepository(ABC):
    @abstractmethod
    def save(self, trip: Trip) -> Trip:
        pass

    @abstractmethod
    def find_by_id(self, trip_id: int) -> Optional[Trip]:
        pass

    @abstractmethod
    def get_max_trip_number_for_date(self, vehicle_id: int, trip_date: date) -> int:
        """Get the highest trip number for a vehicle on a specific date.
        Returns 0 if no trips exist for that date."""
        pass

    @abstractmethod
    def find_by_vehicle_and_date_range(
        self,
        vehicle_id: int,
        start_date: date,
        end_date: date
    ) -> List[Trip]:
        pass

    @abstractmethod
    def count_by_vehicle_and_date(self, vehicle_id: int, trip_date: date) -> int:
        pass

    @abstractmethod
    def find_by_group_and_date(self, group_id: int, trip_date: date) -> List[Trip]:
        """Find all trips for a group on a specific date."""
        pass

    @abstractmethod
    def find_by_group_and_date_range(
        self,
        group_id: int,
        start_date: date,
        end_date: date
    ) -> List[Trip]:
        """Find all trips for a group within a date range."""
        pass

    @abstractmethod
    def has_trips_for_vehicle(self, vehicle_id: int) -> bool:
        """Check if any trips exist for the vehicle."""
        pass

    @abstractmethod
    def has_trips_for_driver(self, driver_id: int) -> bool:
        """Check if any trips exist for the driver."""
        pass
