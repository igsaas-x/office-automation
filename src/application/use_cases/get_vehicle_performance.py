from datetime import date, timedelta
from typing import Dict
from collections import defaultdict
import calendar
from ...domain.repositories.vehicle_repository import IVehicleRepository
from ...domain.repositories.driver_repository import IDriverRepository
from ...domain.repositories.trip_repository import ITripRepository
from ...domain.repositories.fuel_record_repository import IFuelRecordRepository
from ..dto.report_dto import VehiclePerformanceResponse, DailyBreakdown

class GetVehiclePerformanceUseCase:
    def __init__(
        self,
        vehicle_repository: IVehicleRepository,
        driver_repository: IDriverRepository,
        trip_repository: ITripRepository,
        fuel_record_repository: IFuelRecordRepository
    ):
        self.vehicle_repository = vehicle_repository
        self.driver_repository = driver_repository
        self.trip_repository = trip_repository
        self.fuel_record_repository = fuel_record_repository

    def execute(self, vehicle_id: int) -> VehiclePerformanceResponse:
        # Get vehicle
        vehicle = self.vehicle_repository.find_by_id(vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle with ID {vehicle_id} not found")

        # Get driver name if assigned
        driver_name = None
        drivers = self.driver_repository.find_by_group_id(vehicle.group_id)
        for driver in drivers:
            if driver.assigned_vehicle_id == vehicle.id:
                driver_name = driver.name
                break

        # Get current month data
        today = date.today()
        first_day_of_month = date(today.year, today.month, 1)
        last_day_of_month = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])

        month_trips = self.trip_repository.find_by_vehicle_and_date_range(
            vehicle_id, first_day_of_month, last_day_of_month
        )
        month_fuel = self.fuel_record_repository.find_by_vehicle_and_date_range(
            vehicle_id, first_day_of_month, last_day_of_month
        )

        # Calculate month totals
        month_total_trips = len(month_trips)
        month_total_loading_size = sum(t.loading_size_cubic_meters or 0 for t in month_trips)
        month_total_fuel = sum(f.liters for f in month_fuel)
        month_total_cost = sum(f.cost for f in month_fuel)

        # Calculate month averages
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        month_avg_trips_per_day = month_total_trips / days_in_month if days_in_month > 0 else 0
        month_avg_fuel_per_trip = month_total_fuel / month_total_trips if month_total_trips > 0 else 0
        month_avg_cost_per_trip = month_total_cost / month_total_trips if month_total_trips > 0 else 0

        # Get last 7 days data
        seven_days_ago = today - timedelta(days=6)  # Including today = 7 days
        last_7_days_trips = self.trip_repository.find_by_vehicle_and_date_range(
            vehicle_id, seven_days_ago, today
        )
        last_7_days_fuel = self.fuel_record_repository.find_by_vehicle_and_date_range(
            vehicle_id, seven_days_ago, today
        )

        # Aggregate last 7 days by date
        daily_data: Dict[date, dict] = defaultdict(lambda: {
            'trips': 0,
            'total_loading_size': 0.0,
            'fuel_liters': 0.0,
            'fuel_cost': 0.0
        })

        for trip in last_7_days_trips:
            daily_data[trip.date]['trips'] += 1
            if trip.loading_size_cubic_meters:
                daily_data[trip.date]['total_loading_size'] += trip.loading_size_cubic_meters

        for fuel in last_7_days_fuel:
            daily_data[fuel.date]['fuel_liters'] += fuel.liters
            daily_data[fuel.date]['fuel_cost'] += fuel.cost

        # Create daily breakdown (last 7 days, most recent first)
        daily_breakdowns = []
        for i in range(6, -1, -1):  # 6 down to 0 for reverse chronological order
            check_date = today - timedelta(days=i)
            data = daily_data[check_date]
            daily_breakdowns.append(DailyBreakdown(
                date=check_date.isoformat(),
                trips=data['trips'],
                total_loading_size=data['total_loading_size'],
                fuel_liters=data['fuel_liters'],
                fuel_cost=data['fuel_cost']
            ))

        return VehiclePerformanceResponse(
            vehicle_id=vehicle.id,
            license_plate=vehicle.license_plate,
            vehicle_type=vehicle.vehicle_type,
            driver_name=driver_name,
            month_total_trips=month_total_trips,
            month_total_loading_size=round(month_total_loading_size, 1),
            month_total_fuel=round(month_total_fuel, 1),
            month_total_cost=round(month_total_cost, 2),
            month_avg_trips_per_day=round(month_avg_trips_per_day, 1),
            month_avg_fuel_per_trip=round(month_avg_fuel_per_trip, 1),
            month_avg_cost_per_trip=round(month_avg_cost_per_trip, 2),
            last_7_days=daily_breakdowns
        )
