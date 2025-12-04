from datetime import date
from typing import Dict
from collections import defaultdict
from ...domain.repositories.vehicle_repository import IVehicleRepository
from ...domain.repositories.driver_repository import IDriverRepository
from ...domain.repositories.trip_repository import ITripRepository
from ...domain.repositories.fuel_record_repository import IFuelRecordRepository
from ..dto.report_dto import (
    DailyReportResponse,
    VehicleDailySummary,
    TripDailyDetail,
    FuelDailyDetail
)

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

        # Get all vehicles/drivers for the group
        vehicles = self.vehicle_repository.find_by_group_id(group_id)
        vehicle_map = {v.id: v for v in vehicles}

        drivers = self.driver_repository.find_by_group_id(group_id)
        driver_map = {d.id: d for d in drivers}

        driver_by_vehicle = {
            d.assigned_vehicle_id: d
            for d in drivers
            if d.assigned_vehicle_id is not None
        }

        # Get all trips and fuel records for the date
        trips = self.trip_repository.find_by_group_and_date(group_id, report_date)
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
            driver = driver_by_vehicle.get(vehicle.id)
            driver_name = driver.name if driver else None

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

        # Detailed lists
        trip_details = []
        for trip in sorted(trips, key=lambda t: t.created_at):
            vehicle = vehicle_map.get(trip.vehicle_id)
            driver = driver_map.get(trip.driver_id)
            trip_details.append(TripDailyDetail(
                vehicle_plate=vehicle.license_plate if vehicle else "Unknown",
                driver_name=driver.name if driver else None,
                trip_number=trip.trip_number,
                created_at=trip.created_at.isoformat()
            ))

        fuel_details = []
        for record in sorted(fuel_records, key=lambda f: f.created_at):
            vehicle = vehicle_map.get(record.vehicle_id)
            fuel_details.append(FuelDailyDetail(
                vehicle_plate=vehicle.license_plate if vehicle else "Unknown",
                liters=record.liters,
                cost=record.cost,
                created_at=record.created_at.isoformat()
            ))

        return DailyReportResponse(
            date=report_date.isoformat(),
            vehicles=vehicle_summaries,
            trips=trip_details,
            fuel_records=fuel_details,
            total_trips=total_trips,
            total_fuel_liters=total_fuel_liters,
            total_fuel_cost=total_fuel_cost
        )
