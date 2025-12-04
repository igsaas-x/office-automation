from dataclasses import dataclass
from typing import List, Optional

@dataclass
class VehicleDailySummary:
    vehicle_id: int
    license_plate: str
    vehicle_type: str
    driver_name: Optional[str]
    trip_count: int
    total_fuel_liters: float
    total_fuel_cost: float

@dataclass
class DailyReportResponse:
    date: str
    vehicles: List[VehicleDailySummary]
    total_trips: int
    total_fuel_liters: float
    total_fuel_cost: float

@dataclass
class VehicleMonthlySummary:
    vehicle_id: int
    license_plate: str
    vehicle_type: str
    driver_name: Optional[str]
    total_trips: int
    total_fuel_liters: float
    total_fuel_cost: float
    avg_trips_per_day: float
    avg_fuel_per_trip: float

@dataclass
class MonthlyReportResponse:
    year: int
    month: int
    vehicles: List[VehicleMonthlySummary]
    total_vehicles: int
    total_trips: int
    total_fuel_liters: float
    total_fuel_cost: float

@dataclass
class DailyBreakdown:
    date: str
    trips: int
    fuel_liters: float
    fuel_cost: float

@dataclass
class VehiclePerformanceResponse:
    vehicle_id: int
    license_plate: str
    vehicle_type: str
    driver_name: Optional[str]
    # This month stats
    month_total_trips: int
    month_total_fuel: float
    month_total_cost: float
    month_avg_trips_per_day: float
    month_avg_fuel_per_trip: float
    month_avg_cost_per_trip: float
    # Last 7 days breakdown
    last_7_days: List[DailyBreakdown]
