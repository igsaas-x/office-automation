from datetime import date
from typing import Dict
from collections import defaultdict
import calendar
from ...domain.repositories.vehicle_repository import IVehicleRepository
from ...domain.repositories.driver_repository import IDriverRepository
from ...domain.repositories.trip_repository import ITripRepository
from ...domain.repositories.fuel_record_repository import IFuelRecordRepository
from ..dto.report_dto import MonthlyReportResponse, VehicleMonthlySummary

class GetMonthlyReportUseCase:
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

    def execute(self, group_id: int, year: int = None, month: int = None) -> MonthlyReportResponse:
        if year is None or month is None:
            today = date.today()
            year = today.year
            month = today.month

        # Get first and last day of the month
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])

        # Get all vehicles for the group
        vehicles = self.vehicle_repository.find_by_group_id(group_id)

        # Get all trips for the month
        trips = self.trip_repository.find_by_group_and_date_range(group_id, first_day, last_day)

        # Get all fuel records for the month
        fuel_records = self.fuel_record_repository.find_by_group_and_date_range(group_id, first_day, last_day)

        # Aggregate data by vehicle
        vehicle_data: Dict[int, dict] = defaultdict(lambda: {
            'trip_count': 0,
            'total_loading_size': 0.0,
            'total_fuel_liters': 0.0,
            'total_fuel_cost': 0.0
        })

        # Count trips and sum loading size per vehicle
        for trip in trips:
            vehicle_data[trip.vehicle_id]['trip_count'] += 1
            if trip.loading_size_cubic_meters:
                vehicle_data[trip.vehicle_id]['total_loading_size'] += trip.loading_size_cubic_meters

        # Sum fuel per vehicle
        for fuel_record in fuel_records:
            vehicle_data[fuel_record.vehicle_id]['total_fuel_liters'] += fuel_record.liters
            vehicle_data[fuel_record.vehicle_id]['total_fuel_cost'] += fuel_record.cost

        # Create vehicle summaries
        vehicle_summaries = []
        total_trips = 0
        total_fuel_liters = 0.0
        total_fuel_cost = 0.0

        days_in_month = calendar.monthrange(year, month)[1]

        for vehicle in vehicles:
            data = vehicle_data[vehicle.id]

            # Get driver name if assigned
            driver_name = None
            drivers = self.driver_repository.find_by_group_id(group_id)
            for driver in drivers:
                if driver.assigned_vehicle_id == vehicle.id:
                    driver_name = driver.name
                    break

            # Calculate averages
            avg_trips_per_day = data['trip_count'] / days_in_month if days_in_month > 0 else 0
            avg_fuel_per_trip = (
                data['total_fuel_liters'] / data['trip_count']
                if data['trip_count'] > 0 else 0
            )

            vehicle_summaries.append(VehicleMonthlySummary(
                vehicle_id=vehicle.id,
                license_plate=vehicle.license_plate,
                vehicle_type=vehicle.vehicle_type,
                driver_name=driver_name,
                total_trips=data['trip_count'],
                total_loading_size=data['total_loading_size'],
                total_fuel_liters=data['total_fuel_liters'],
                total_fuel_cost=data['total_fuel_cost'],
                avg_trips_per_day=round(avg_trips_per_day, 1),
                avg_fuel_per_trip=round(avg_fuel_per_trip, 1)
            ))

            total_trips += data['trip_count']
            total_fuel_liters += data['total_fuel_liters']
            total_fuel_cost += data['total_fuel_cost']

        return MonthlyReportResponse(
            year=year,
            month=month,
            days_in_month=days_in_month,
            vehicles=vehicle_summaries,
            total_vehicles=len(vehicles),
            total_trips=total_trips,
            total_fuel_liters=total_fuel_liters,
            total_fuel_cost=total_fuel_cost
        )
