"""
Vehicle Operations Handler Wrappers
Contains handlers for trip and fuel recording
"""
from telegram import Update
from telegram.ext import ContextTypes
from ....application.use_cases.record_trip import RecordTripUseCase
from ....application.use_cases.record_fuel import RecordFuelUseCase
from ....presentation.handlers.vehicle_operations_handler import VehicleOperationsHandler


def create_vehicle_operations_wrappers(get_repositories_func):
    """
    Create vehicle operations handler wrappers

    Args:
        get_repositories_func: Function that returns repository tuple

    Returns:
        Dict of wrapper functions
    """

    # Trip recording handlers
    async def start_trip_recording_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo, _ = get_repositories_func()
        vehicle_ops_handler = VehicleOperationsHandler(
            RecordTripUseCase(trip_repo, vehicle_repo),
            RecordFuelUseCase(None, vehicle_repo),  # fuel_repo passed later
            vehicle_repo
        )
        result = await vehicle_ops_handler.start_trip_recording(update, context)
        session.close()
        return result

    async def select_trip_vehicle_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo, _ = get_repositories_func()
        vehicle_ops_handler = VehicleOperationsHandler(
            RecordTripUseCase(trip_repo, vehicle_repo),
            RecordFuelUseCase(None, vehicle_repo),
            vehicle_repo
        )
        result = await vehicle_ops_handler.select_trip_vehicle(update, context)
        session.close()
        return result

    async def receive_trip_count_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo, _ = get_repositories_func()
        vehicle_ops_handler = VehicleOperationsHandler(
            RecordTripUseCase(trip_repo, vehicle_repo),
            RecordFuelUseCase(None, vehicle_repo),
            vehicle_repo
        )
        result = await vehicle_ops_handler.receive_trip_count(update, context)
        session.close()
        return result

    async def receive_total_loading_size_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo, _ = get_repositories_func()
        vehicle_ops_handler = VehicleOperationsHandler(
            RecordTripUseCase(trip_repo, vehicle_repo),
            RecordFuelUseCase(None, vehicle_repo),
            vehicle_repo
        )
        result = await vehicle_ops_handler.receive_total_loading_size(update, context)
        session.close()
        return result

    # Fuel recording handlers
    async def start_fuel_recording_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo, _ = get_repositories_func()
        vehicle_ops_handler = VehicleOperationsHandler(
            RecordTripUseCase(None, vehicle_repo),
            RecordFuelUseCase(fuel_repo, vehicle_repo),
            vehicle_repo
        )
        result = await vehicle_ops_handler.start_fuel_recording(update, context)
        session.close()
        return result

    async def select_fuel_vehicle_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo, _ = get_repositories_func()
        vehicle_ops_handler = VehicleOperationsHandler(
            RecordTripUseCase(None, vehicle_repo),
            RecordFuelUseCase(fuel_repo, vehicle_repo),
            vehicle_repo
        )
        result = await vehicle_ops_handler.select_fuel_vehicle(update, context)
        session.close()
        return result

    async def receive_fuel_liters_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo, _ = get_repositories_func()
        vehicle_ops_handler = VehicleOperationsHandler(
            RecordTripUseCase(None, vehicle_repo),
            RecordFuelUseCase(fuel_repo, vehicle_repo),
            vehicle_repo
        )
        result = await vehicle_ops_handler.receive_fuel_liters(update, context)
        session.close()
        return result

    async def receive_fuel_cost_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo, _ = get_repositories_func()
        vehicle_ops_handler = VehicleOperationsHandler(
            RecordTripUseCase(None, vehicle_repo),
            RecordFuelUseCase(fuel_repo, vehicle_repo),
            vehicle_repo
        )
        result = await vehicle_ops_handler.receive_fuel_cost(update, context)
        session.close()
        return result

    async def complete_fuel_record_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo, _ = get_repositories_func()
        vehicle_ops_handler = VehicleOperationsHandler(
            RecordTripUseCase(None, vehicle_repo),
            RecordFuelUseCase(fuel_repo, vehicle_repo),
            vehicle_repo
        )
        result = await vehicle_ops_handler.complete_fuel_record(update, context)
        session.close()
        return result

    return {
        'start_trip_recording_wrapper': start_trip_recording_wrapper,
        'select_trip_vehicle_wrapper': select_trip_vehicle_wrapper,
        'receive_trip_count_wrapper': receive_trip_count_wrapper,
        'receive_total_loading_size_wrapper': receive_total_loading_size_wrapper,
        'start_fuel_recording_wrapper': start_fuel_recording_wrapper,
        'select_fuel_vehicle_wrapper': select_fuel_vehicle_wrapper,
        'receive_fuel_liters_wrapper': receive_fuel_liters_wrapper,
        'receive_fuel_cost_wrapper': receive_fuel_cost_wrapper,
        'complete_fuel_record_wrapper': complete_fuel_record_wrapper,
    }
