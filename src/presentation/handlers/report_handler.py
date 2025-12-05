from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler
from typing import Optional
from datetime import date
from html import escape
from ...application.use_cases.get_daily_report import GetDailyReportUseCase
from ...application.use_cases.get_monthly_report import GetMonthlyReportUseCase
from ...application.use_cases.get_vehicle_performance import GetVehiclePerformanceUseCase
from ...domain.repositories.vehicle_repository import IVehicleRepository
from ...domain.repositories.driver_repository import IDriverRepository

# Conversation states
SELECT_VEHICLE_FOR_PERFORMANCE = 51

class ReportHandler:
    def __init__(
        self,
        daily_report_use_case: GetDailyReportUseCase,
        monthly_report_use_case: GetMonthlyReportUseCase,
        vehicle_performance_use_case: GetVehiclePerformanceUseCase,
        vehicle_repository: IVehicleRepository,
        driver_repository: Optional[IDriverRepository] = None
    ):
        self.daily_report_use_case = daily_report_use_case
        self.monthly_report_use_case = monthly_report_use_case
        self.vehicle_performance_use_case = vehicle_performance_use_case
        self.vehicle_repository = vehicle_repository
        self.driver_repository = driver_repository

    # ==================== Daily Report ====================

    async def show_daily_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show daily report for today"""
        query = update.callback_query
        if query:
            await query.answer()

        chat = update.effective_chat

        # Get group from database
        from ...infrastructure.persistence.database import database
        from ...infrastructure.persistence.group_repository_impl import GroupRepository

        session = database.get_session()
        group_repo = GroupRepository(session)
        group = group_repo.find_by_chat_id(str(chat.id))

        if not group:
            message = "❌ Error: Group not found. Please register first."
            if query:
                await query.edit_message_text(message)
            else:
                await update.message.reply_text(message)
            session.close()
            return

        try:
            # Get daily report for today
            today = date.today()
            report = self.daily_report_use_case.execute(group.id, today)

            # Format report message
            message_parts = [
                f"📅 Daily Report - {escape(report.date)}",
                "",
                "📊 Summary:",
                f"• Total Trips: {report.total_trips}",
                f"• Total Fuel: {report.total_fuel_liters}L",
                f"• Total Cost: ${report.total_fuel_cost:,.2f}",
                ""
            ]

            if not report.vehicles:
                message_parts.append("⚠️ No activity recorded for today.")
            else:
                # Create consolidated table
                table_lines = []
                table_lines.append("Vehicle/Driver|Trips|Fuel(L/$)")
                table_lines.append("-------------------------------")

                for vehicle_data in report.vehicles:
                    # Format vehicle/driver column
                    vehicle_str = f"{vehicle_data.license_plate}"
                    if vehicle_data.driver_name:
                        # Show last 5 chars of driver name if longer than 5
                        driver_name = vehicle_data.driver_name[-5:] if len(vehicle_data.driver_name) > 5 else vehicle_data.driver_name
                        vehicle_str += f"/{driver_name}"

                    # Format trips column as "count/loadingm³"
                    if vehicle_data.total_loading_size > 0:
                        trips_str = f"{vehicle_data.trip_count}/{vehicle_data.total_loading_size:.0f}m³"
                    else:
                        trips_str = f"{vehicle_data.trip_count}"

                    # Format fuel column
                    if vehicle_data.total_fuel_liters > 0:
                        fuel_str = f"{vehicle_data.total_fuel_liters:.0f}L/{vehicle_data.total_fuel_cost:.0f}$"
                    else:
                        fuel_str = "—"

                    # Build the row with pipe separators
                    table_lines.append(f"{vehicle_str:<14}|{trips_str:^11}| {fuel_str}")

                message_parts.append("<pre>")
                message_parts.append(escape('\n'.join(table_lines)))
                message_parts.append("</pre>")

            message_text = "\n".join(message_parts)

            # Display report without buttons (end of session)
            if query:
                await query.edit_message_text(message_text, parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text(message_text, parse_mode=ParseMode.HTML)

        except Exception as e:
            error_message = f"❌ Error generating report: {str(e)}"
            if query:
                await query.edit_message_text(error_message)
            else:
                await update.message.reply_text(error_message)
        finally:
            session.close()

    # ==================== Monthly Report ====================

    async def show_monthly_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show monthly report for current month"""
        query = update.callback_query
        if query:
            await query.answer()

        chat = update.effective_chat

        # Get group from database
        from ...infrastructure.persistence.database import database
        from ...infrastructure.persistence.group_repository_impl import GroupRepository

        session = database.get_session()
        group_repo = GroupRepository(session)
        group = group_repo.find_by_chat_id(str(chat.id))

        if not group:
            message = "❌ Error: Group not found. Please register first."
            if query:
                await query.edit_message_text(message)
            else:
                await update.message.reply_text(message)
            session.close()
            return

        try:
            # Get monthly report for current month
            today = date.today()
            report = self.monthly_report_use_case.execute(group.id, today.year, today.month)

            # Format report message
            month_names = {
                1: "January", 2: "February", 3: "March", 4: "April",
                5: "May", 6: "June", 7: "July", 8: "August",
                9: "September", 10: "October", 11: "November", 12: "December"
            }

            message_text = (
                f"📆 Monthly Report - {month_names[report.month]} {report.year}\n\n"
                f"📊 Summary:\n"
                f"• Total Vehicles: {report.total_vehicles}\n"
                f"• Total Trips: {report.total_trips}\n"
                f"• Total Fuel: {report.total_fuel_liters}L\n"
                f"• Total Cost: ${report.total_fuel_cost:,.2f}\n"
            )

            if report.total_trips > 0:
                avg_trips_per_day = report.total_trips / report.days_in_month
                message_text += f"• Avg Trips/Day: {avg_trips_per_day:.1f}\n"

            if report.vehicles:
                message_text += "\n\n🚗 Vehicle Performance:\n"
                type_emoji = {"TRUCK": "🚚", "VAN": "🚐", "MOTORCYCLE": "🏍️", "CAR": "🚗"}

                # Sort by total trips descending
                sorted_vehicles = sorted(report.vehicles, key=lambda v: v.total_trips, reverse=True)

                for vehicle_data in sorted_vehicles:
                    emoji = type_emoji.get(vehicle_data.vehicle_type, "🚗")
                    # Format trips as "count/loadingm³"
                    if vehicle_data.total_loading_size > 0:
                        trips_display = f"{vehicle_data.total_trips}/{vehicle_data.total_loading_size:.0f}m³"
                    else:
                        trips_display = f"{vehicle_data.total_trips}"

                    message_text += (
                        f"\n{emoji} {vehicle_data.license_plate}\n"
                        f"  • Trips: {trips_display}\n"
                    )
                    if vehicle_data.total_fuel_liters > 0:
                        message_text += (
                            f"  • Fuel: {vehicle_data.total_fuel_liters}L\n"
                            f"  • Cost: ${vehicle_data.total_fuel_cost:,.2f}\n"
                        )
                        if vehicle_data.total_trips > 0:
                            avg_fuel_per_trip = vehicle_data.total_fuel_liters / vehicle_data.total_trips
                            message_text += f"  • Avg Fuel/Trip: {avg_fuel_per_trip:.1f}L\n"
                    if vehicle_data.driver_name:
                        message_text += f"  • Driver: {vehicle_data.driver_name}\n"
            else:
                message_text += "\n\n⚠️ No activity recorded for this month."

            # Display report without buttons (end of session)
            if query:
                await query.edit_message_text(message_text)
            else:
                await update.message.reply_text(message_text)

        except Exception as e:
            error_message = f"❌ Error generating report: {str(e)}"
            if query:
                await query.edit_message_text(error_message)
            else:
                await update.message.reply_text(error_message)
        finally:
            session.close()

    # ==================== Vehicle Performance Report ====================

    async def start_vehicle_performance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start vehicle performance report flow - show vehicle selection"""
        query = update.callback_query
        if query:
            await query.answer()

        chat = update.effective_chat
        context.user_data['report_group_id'] = chat.id

        # Get group from database
        from ...infrastructure.persistence.database import database
        from ...infrastructure.persistence.group_repository_impl import GroupRepository

        session = database.get_session()
        group_repo = GroupRepository(session)
        group = group_repo.find_by_chat_id(str(chat.id))

        if not group:
            message = "❌ Error: Group not found. Please register first."
            if query:
                await query.edit_message_text(message)
            else:
                await update.message.reply_text(message)
            session.close()
            return ConversationHandler.END

        # Get all vehicles
        vehicles = self.vehicle_repository.find_by_group_id(group.id)
        session.close()

        if not vehicles:
            message = (
                "⚠️ No vehicles found!\n\n"
                "Please setup a vehicle first using /setup"
            )
            if query:
                await query.edit_message_text(message)
            else:
                await update.message.reply_text(message)
            return ConversationHandler.END

        # Show vehicle selection
        keyboard = []
        type_emoji = {"TRUCK": "🚚", "VAN": "🚐", "MOTORCYCLE": "🏍️", "CAR": "🚗"}
        for vehicle in vehicles:
            emoji = type_emoji.get(vehicle.vehicle_type, "🚗")
            # Get driver name
            drivers = self.driver_repository.find_by_group_id(group.id)
            driver_name = None
            for driver in drivers:
                if driver.assigned_vehicle_id == vehicle.id:
                    driver_name = driver.name
                    break

            label = f"{emoji} {vehicle.license_plate}"
            if driver_name:
                label += f" ({driver_name})"

            keyboard.append([
                InlineKeyboardButton(label, callback_data=f"perf_vehicle_{vehicle.id}")
            ])

        keyboard.append([InlineKeyboardButton("🏠 Back to Menu", callback_data="back_to_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        message_text = "📈 Vehicle Performance Report\n\nSelect vehicle:"

        if query:
            await query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)

        return SELECT_VEHICLE_FOR_PERFORMANCE

    async def show_vehicle_performance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show detailed performance report for selected vehicle"""
        query = update.callback_query
        await query.answer()

        vehicle_id = int(query.data.replace("perf_vehicle_", ""))

        try:
            # Get vehicle performance report
            report = self.vehicle_performance_use_case.execute(vehicle_id)

            # Format report message
            type_emoji = {"TRUCK": "🚚", "VAN": "🚐", "MOTORCYCLE": "🏍️", "CAR": "🚗"}
            emoji = type_emoji.get(report.vehicle_type, "🚗")

            message_text = (
                f"📈 Vehicle Performance Report\n\n"
                f"{emoji} {report.license_plate}\n"
            )

            if report.driver_name:
                message_text += f"👤 Driver: {report.driver_name}\n"

            # Format trips as "count/loadingm³"
            if report.month_total_loading_size > 0:
                trips_display = f"{report.month_total_trips}/{report.month_total_loading_size:.0f}m³"
            else:
                trips_display = f"{report.month_total_trips}"

            message_text += (
                f"\n📊 This Month Summary:\n"
                f"• Total Trips: {trips_display}\n"
            )

            if report.month_total_fuel > 0:
                message_text += (
                    f"• Total Fuel: {report.month_total_fuel}L\n"
                    f"• Total Cost: ${report.month_total_cost:,.2f}\n"
                )

            message_text += (
                f"• Avg Trips/Day: {report.month_avg_trips_per_day:.1f}\n"
            )

            if report.month_avg_fuel_per_trip > 0:
                message_text += (
                    f"• Avg Fuel/Trip: {report.month_avg_fuel_per_trip:.1f}L\n"
                    f"• Avg Cost/Trip: ${report.month_avg_cost_per_trip:,.2f}\n"
                )

            # Show last 7 days breakdown
            message_text += "\n\n📅 Last 7 Days:\n"
            for day_data in report.last_7_days:
                # Format date as day name
                from datetime import datetime
                day_date = datetime.fromisoformat(day_data.date)
                day_name = day_date.strftime("%a %d/%m")

                if day_data.trips > 0 or day_data.fuel_liters > 0:
                    message_text += f"\n{day_name}:\n"
                    if day_data.trips > 0:
                        # Format trips as "count/loadingm³"
                        if day_data.total_loading_size > 0:
                            trips_display = f"{day_data.trips}/{day_data.total_loading_size:.0f}m³"
                        else:
                            trips_display = f"{day_data.trips}"
                        message_text += f"  • Trips: {trips_display}\n"
                    if day_data.fuel_liters > 0:
                        message_text += f"  • Fuel: {day_data.fuel_liters}L (${day_data.fuel_cost:,.2f})\n"

            # Display report without buttons (end of session)
            await query.edit_message_text(message_text)

        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)}")

        return ConversationHandler.END

    # ==================== Export Handlers (Placeholders) ====================

    async def export_placeholder(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Placeholder for export functionality"""
        query = update.callback_query
        await query.answer()

        export_type = "Excel" if "excel" in query.data else "PDF"

        await query.answer(
            f"📊 {export_type} export feature coming soon!",
            show_alert=True
        )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel operation"""
        await update.message.reply_text("Operation cancelled.")
        return ConversationHandler.END
