"""
Report Handler Wrappers
Contains handlers for vehicle logistics reports
"""
from telegram import Update
from telegram.ext import ContextTypes
from ....application.use_cases.get_daily_report import GetDailyReportUseCase
from ....application.use_cases.get_monthly_report import GetMonthlyReportUseCase
from ....application.use_cases.get_vehicle_performance import GetVehiclePerformanceUseCase
from ....presentation.handlers.report_handler import ReportHandler


def create_report_wrappers(get_repositories_func):
    """
    Create report handler wrappers

    Args:
        get_repositories_func: Function that returns repository tuple

    Returns:
        Dict of wrapper functions
    """

    async def show_daily_report_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo, _ = get_repositories_func()
        report_handler = ReportHandler(
            GetDailyReportUseCase(vehicle_repo, None, trip_repo, fuel_repo),
            GetMonthlyReportUseCase(vehicle_repo, None, trip_repo, fuel_repo),
            GetVehiclePerformanceUseCase(vehicle_repo, None, trip_repo, fuel_repo),
            vehicle_repo, None
        )
        await report_handler.show_daily_report(update, context)
        session.close()

    async def show_monthly_report_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo, _ = get_repositories_func()
        report_handler = ReportHandler(
            GetDailyReportUseCase(vehicle_repo, None, trip_repo, fuel_repo),
            GetMonthlyReportUseCase(vehicle_repo, None, trip_repo, fuel_repo),
            GetVehiclePerformanceUseCase(vehicle_repo, None, trip_repo, fuel_repo),
            vehicle_repo, None
        )
        await report_handler.show_monthly_report(update, context)
        session.close()

    async def start_vehicle_performance_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo, _ = get_repositories_func()
        report_handler = ReportHandler(
            GetDailyReportUseCase(vehicle_repo, None, trip_repo, fuel_repo),
            GetMonthlyReportUseCase(vehicle_repo, None, trip_repo, fuel_repo),
            GetVehiclePerformanceUseCase(vehicle_repo, None, trip_repo, fuel_repo),
            vehicle_repo, None
        )
        result = await report_handler.start_vehicle_performance(update, context)
        session.close()
        return result

    async def show_vehicle_performance_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo, _ = get_repositories_func()
        report_handler = ReportHandler(
            GetDailyReportUseCase(vehicle_repo, None, trip_repo, fuel_repo),
            GetMonthlyReportUseCase(vehicle_repo, None, trip_repo, fuel_repo),
            GetVehiclePerformanceUseCase(vehicle_repo, None, trip_repo, fuel_repo),
            vehicle_repo, None
        )
        result = await report_handler.show_vehicle_performance(update, context)
        session.close()
        return result

    async def export_placeholder_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo, _ = get_repositories_func()
        report_handler = ReportHandler(
            GetDailyReportUseCase(vehicle_repo, None, trip_repo, fuel_repo),
            GetMonthlyReportUseCase(vehicle_repo, None, trip_repo, fuel_repo),
            GetVehiclePerformanceUseCase(vehicle_repo, None, trip_repo, fuel_repo),
            vehicle_repo, None
        )
        await report_handler.export_placeholder(update, context)
        session.close()

    return {
        'show_daily_report_wrapper': show_daily_report_wrapper,
        'show_monthly_report_wrapper': show_monthly_report_wrapper,
        'start_vehicle_performance_wrapper': start_vehicle_performance_wrapper,
        'show_vehicle_performance_wrapper': show_vehicle_performance_wrapper,
        'export_placeholder_wrapper': export_placeholder_wrapper,
    }
