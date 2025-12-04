from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.vehicle import Vehicle

class IVehicleRepository(ABC):
    @abstractmethod
    def save(self, vehicle: Vehicle) -> Vehicle:
        pass

    @abstractmethod
    def find_by_id(self, vehicle_id: int) -> Optional[Vehicle]:
        pass

    @abstractmethod
    def find_by_group_id(self, group_id: int) -> List[Vehicle]:
        pass

    @abstractmethod
    def find_by_license_plate(self, group_id: int, license_plate: str) -> Optional[Vehicle]:
        pass
