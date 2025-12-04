from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import date
from ..entities.fuel_record import FuelRecord

class IFuelRecordRepository(ABC):
    @abstractmethod
    def save(self, fuel_record: FuelRecord) -> FuelRecord:
        pass

    @abstractmethod
    def find_by_id(self, fuel_record_id: int) -> Optional[FuelRecord]:
        pass

    @abstractmethod
    def find_by_vehicle_and_date_range(
        self,
        vehicle_id: int,
        start_date: date,
        end_date: date
    ) -> List[FuelRecord]:
        pass

    @abstractmethod
    def find_by_group_and_date(self, group_id: int, fuel_date: date) -> List[FuelRecord]:
        """Find all fuel records for a group on a specific date."""
        pass

    @abstractmethod
    def find_by_group_and_date_range(
        self,
        group_id: int,
        start_date: date,
        end_date: date
    ) -> List[FuelRecord]:
        """Find all fuel records for a group within a date range."""
        pass

    @abstractmethod
    def has_records_for_vehicle(self, vehicle_id: int) -> bool:
        """Check if any fuel records exist for the vehicle."""
        pass
