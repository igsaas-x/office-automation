from datetime import date
from typing import Dict
from collections import defaultdict
from ...domain.repositories.vehicle_repository import IVehicleRepository
from ...domain.repositories.driver_repository import IDriverRepository
from ...domain.repositories.trip_repository import ITripRepository
from ...domain.repositories.fuel_record_repository import IFuelRecordRepository
from ..dto.report_dto import DailyReportResponse, VehicleDailySummary

class GetDailyReportUseCase:
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

    def execute(self, group_id: int, report_date: date = None) -> DailyReportResponse:
        if report_date is None:
            report_date = date.today()

        # Get all vehicles for the group
        vehicles = self.vehicle_repository.find_by_group_id(group_id)

        # Get all trips for the date
        trips = self.trip_repository.find_by_group_and_date(group_id, report_date)

        # Get all fuel records for the date
        fuel_records = self.fuel_record_repository.find_by_group_and_date(group_id, report_date)

        # Aggregate data by vehicle
        vehicle_data: Dict[int, dict] = defaultdict(lambda: {
            'trip_count': 0,
            'total_fuel_liters': 0.0,
            'total_fuel_cost': 0.0
        })

        # Count trips per vehicle
        for trip in trips:
            vehicle_data[trip.vehicle_id]['trip_count'] += 1

        # Sum fuel per vehicle
        for fuel_record in fuel_records:
            vehicle_data[fuel_record.vehicle_id]['total_fuel_liters'] += fuel_record.liters
            vehicle_data[fuel_record.vehicle_id]['total_fuel_cost'] += fuel_record.cost

        # Create vehicle summaries
        vehicle_summaries = []
        total_trips = 0
        total_fuel_liters = 0.0
        total_fuel_cost = 0.0

        for vehicle in vehicles:
            data = vehicle_data[vehicle.id]

            # Get driver name if assigned
            driver_name = None
            drivers = self.driver_repository.find_by_group_id(group_id)
            for driver in drivers:
                if driver.assigned_vehicle_id == vehicle.id:
                    driver_name = driver.name
                    break

            vehicle_summaries.append(VehicleDailySummary(
                vehicle_id=vehicle.id,
                license_plate=vehicle.license_plate,
                vehicle_type=vehicle.vehicle_type,
                driver_name=driver_name,
                trip_count=data['trip_count'],
                total_fuel_liters=data['total_fuel_liters'],
                total_fuel_cost=data['total_fuel_cost']
            ))

            total_trips += data['trip_count']
            total_fuel_liters += data['total_fuel_liters']
            total_fuel_cost += data['total_fuel_cost']

        return DailyReportResponse(
            date=report_date.isoformat(),
            vehicles=vehicle_summaries,
            total_trips=total_trips,
            total_fuel_liters=total_fuel_liters,
            total_fuel_cost=total_fuel_cost
        )
