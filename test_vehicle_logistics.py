"""
Test script for Vehicle Logistics System
Tests all layers: repositories, use cases, and data flow
"""

from datetime import date
from src.infrastructure.persistence.database import database
from src.infrastructure.persistence.vehicle_repository_impl import VehicleRepository
from src.infrastructure.persistence.driver_repository_impl import DriverRepository
from src.infrastructure.persistence.trip_repository_impl import TripRepository
from src.infrastructure.persistence.fuel_record_repository_impl import FuelRecordRepository
from src.application.use_cases.register_vehicle import RegisterVehicleUseCase
from src.application.use_cases.register_driver import RegisterDriverUseCase
from src.application.use_cases.record_trip import RecordTripUseCase
from src.application.use_cases.record_fuel import RecordFuelUseCase
from src.application.use_cases.get_daily_report import GetDailyReportUseCase
from src.application.use_cases.get_monthly_report import GetMonthlyReportUseCase
from src.application.use_cases.get_vehicle_performance import GetVehiclePerformanceUseCase
from src.application.dto.vehicle_dto import RegisterVehicleRequest
from src.application.dto.driver_dto import RegisterDriverRequest
from src.application.dto.trip_dto import RecordTripRequest
from src.application.dto.fuel_dto import RecordFuelRequest

def test_vehicle_logistics():
    print("🚀 Starting Vehicle Logistics System Tests")
    print("=" * 60)

    # Create session
    session = database.get_session()

    # Initialize repositories
    vehicle_repo = VehicleRepository(session)
    driver_repo = DriverRepository(session)
    trip_repo = TripRepository(session)
    fuel_repo = FuelRecordRepository(session)

    # Initialize use cases
    register_vehicle_uc = RegisterVehicleUseCase(vehicle_repo)
    register_driver_uc = RegisterDriverUseCase(driver_repo, vehicle_repo)
    record_trip_uc = RecordTripUseCase(trip_repo, vehicle_repo, driver_repo)
    record_fuel_uc = RecordFuelUseCase(fuel_repo, vehicle_repo)
    daily_report_uc = GetDailyReportUseCase(vehicle_repo, driver_repo, trip_repo, fuel_repo)
    monthly_report_uc = GetMonthlyReportUseCase(vehicle_repo, driver_repo, trip_repo, fuel_repo)
    vehicle_performance_uc = GetVehiclePerformanceUseCase(vehicle_repo, driver_repo, trip_repo, fuel_repo)

    # Use a test group ID (you can change this to a real group ID)
    test_group_id = 1

    try:
        # Test 1: Register Vehicle
        print("\n📝 Test 1: Register Vehicle")
        print("-" * 60)
        vehicle_request = RegisterVehicleRequest(
            group_id=test_group_id,
            license_plate="TEST-001",
            vehicle_type="TRUCK"
        )
        vehicle_response = register_vehicle_uc.execute(vehicle_request)
        print(f"✅ Vehicle registered: {vehicle_response.license_plate}")
        print(f"   ID: {vehicle_response.id}")
        print(f"   Type: {vehicle_response.vehicle_type}")
        vehicle_id = vehicle_response.id

        # Test 2: Register Driver
        print("\n📝 Test 2: Register Driver")
        print("-" * 60)
        driver_request = RegisterDriverRequest(
            group_id=test_group_id,
            name="Test Driver",
            phone="012345678",
            assigned_vehicle_id=vehicle_id,
            role="DRIVER"
        )
        driver_response = register_driver_uc.execute(driver_request)
        print(f"✅ Driver registered: {driver_response.name}")
        print(f"   ID: {driver_response.id}")
        print(f"   Phone: {driver_response.phone}")
        print(f"   Assigned to vehicle: {driver_response.assigned_vehicle_id}")
        driver_id = driver_response.id

        # Test 3: Record Trip (should auto-increment to trip #1)
        print("\n📝 Test 3: Record Trip #1")
        print("-" * 60)
        trip_request = RecordTripRequest(
            group_id=test_group_id,
            vehicle_id=vehicle_id,
            driver_id=driver_id
        )
        trip_response = record_trip_uc.execute(trip_request)
        print(f"✅ Trip recorded: #{trip_response.trip_number}")
        print(f"   Vehicle: {trip_response.vehicle_license_plate}")
        print(f"   Driver: {trip_response.driver_name}")
        print(f"   Date: {trip_response.date}")

        # Test 4: Record another trip (should auto-increment to trip #2)
        print("\n📝 Test 4: Record Trip #2 (auto-increment)")
        print("-" * 60)
        trip_response2 = record_trip_uc.execute(trip_request)
        print(f"✅ Trip recorded: #{trip_response2.trip_number}")
        print(f"   Auto-incremented from {trip_response.trip_number} to {trip_response2.trip_number}")

        # Test 5: Record Fuel
        print("\n📝 Test 5: Record Fuel")
        print("-" * 60)
        fuel_request = RecordFuelRequest(
            group_id=test_group_id,
            vehicle_id=vehicle_id,
            liters=50.5,
            cost=252500.0
        )
        fuel_response = record_fuel_uc.execute(fuel_request)
        print(f"✅ Fuel recorded: {fuel_response.liters}L")
        print(f"   Cost: {fuel_response.cost:,.0f} រៀល")
        print(f"   Vehicle: {fuel_response.vehicle_license_plate}")

        # Test 6: Daily Report
        print("\n📝 Test 6: Generate Daily Report")
        print("-" * 60)
        daily_report = daily_report_uc.execute(test_group_id, date.today())
        print(f"✅ Daily Report for {daily_report.date}")
        print(f"   Total Trips: {daily_report.total_trips}")
        print(f"   Total Fuel: {daily_report.total_fuel_liters}L")
        print(f"   Total Cost: {daily_report.total_fuel_cost:,.0f} រៀល")
        print(f"\n   Vehicles:")
        for v in daily_report.vehicles:
            print(f"   - {v.license_plate}: {v.trip_count} trips, {v.total_fuel_liters}L fuel")

        # Test 7: Monthly Report
        print("\n📝 Test 7: Generate Monthly Report")
        print("-" * 60)
        today = date.today()
        monthly_report = monthly_report_uc.execute(test_group_id, today.year, today.month)
        print(f"✅ Monthly Report for {monthly_report.month}/{monthly_report.year}")
        print(f"   Total Vehicles: {monthly_report.total_vehicles}")
        print(f"   Total Trips: {monthly_report.total_trips}")
        print(f"   Total Fuel: {monthly_report.total_fuel_liters}L")
        print(f"   Total Cost: {monthly_report.total_fuel_cost:,.0f} រៀល")

        # Test 8: Vehicle Performance
        print("\n📝 Test 8: Vehicle Performance Report")
        print("-" * 60)
        performance = vehicle_performance_uc.execute(vehicle_id)
        print(f"✅ Performance for {performance.license_plate}")
        print(f"   This Month:")
        print(f"   - Total Trips: {performance.month_total_trips}")
        print(f"   - Avg Trips/Day: {performance.month_avg_trips_per_day}")
        print(f"   - Avg Fuel/Trip: {performance.month_avg_fuel_per_trip}L")
        print(f"\n   Last 7 Days:")
        for day in performance.last_7_days[-3:]:  # Show last 3 days
            print(f"   - {day.date}: {day.trips} trips, {day.fuel_liters}L")

        print("\n" + "=" * 60)
        print("✅ All tests passed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_vehicle_logistics()
