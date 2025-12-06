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
            message = "❌ កំហុស: រកមិនឃើញក្រុម។ សូមចុះឈ្មោះជាមុនសិន។"
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
                f"📅 របាយការណ៍ប្រចាំថ្ងៃ - {escape(report.date)}",
                "",
                "📊 សង្ខេប:",
                f"• ដំណើរសរុប: {report.total_trips}",
                f"• សាំងសរុប: {report.total_fuel_liters}L",
                f"• ចំណាយសរុប: ${report.total_fuel_cost:,.2f}",
                ""
            ]

            if not report.vehicles:
                message_parts.append("⚠️ គ្មានសកម្មភាពកត់ត្រាសម្រាប់ថ្ងៃនេះទេ។")
            else:
                # Create consolidated table
                table_lines = []
                table_lines.append("   ឡាន    |  ចំនួនដឹក  |  ប្រេង(L/$)")
                table_lines.append("-------------------------------")

                for vehicle_data in report.vehicles:
                    # Format vehicle column (plate number only)
                    vehicle_str = vehicle_data.license_plate

                    # Format trips column as "count(loadingm³)"
                    if vehicle_data.total_loading_size > 0:
                        trips_str = f"{vehicle_data.trip_count}({vehicle_data.total_loading_size:.0f}m³)"
                    else:
                        trips_str = str(vehicle_data.trip_count)

                    # Format fuel column
                    if vehicle_data.total_fuel_liters > 0:
                        fuel_str = f"{vehicle_data.total_fuel_liters:.0f}L/{vehicle_data.total_fuel_cost:.0f}$"
                    else:
                        fuel_str = "—"

                    # Build the row with pipe separators and centered alignment
                    table_lines.append(f"{vehicle_str:<10}|{trips_str:^11}| {fuel_str}")

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
            error_message = f"❌ កំហុសក្នុងការបង្កើតរបាយការណ៍: {str(e)}"
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
            message = "❌ កំហុស: រកមិនឃើញក្រុម។ សូមចុះឈ្មោះជាមុនសិន។"
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
                1: "មករា", 2: "កុម្ភៈ", 3: "មីនា", 4: "មេសា",
                5: "ឧសភា", 6: "មិថុនា", 7: "កក្កដា", 8: "សីហា",
                9: "កញ្ញា", 10: "តុលា", 11: "វិច្ឆិកា", 12: "ធ្នូ"
            }

            message_text = (
                f"📆 របាយការណ៍ប្រចាំខែ - {month_names[report.month]} {report.year}\n\n"
                f"📊 សង្ខេប:\n"
                f"• យានជំនិះសរុប: {report.total_vehicles}\n"
                f"• ដំណើរសរុប: {report.total_trips}\n"
                f"• សាំងសរុប: {report.total_fuel_liters}L\n"
                f"• ចំណាយសរុប: ${report.total_fuel_cost:,.2f}\n"
            )

            if report.total_trips > 0:
                avg_trips_per_day = report.total_trips / report.days_in_month
                message_text += f"• មធ្យមដំណើរ/ថ្ងៃ: {avg_trips_per_day:.1f}\n"

            if report.vehicles:
                message_text += "\n"

                # Create table
                table_lines = []
                # table_lines.append("យានជំនិះ  |   ដំណើរ   | សាំង(L/$)")
                table_lines.append("ឡាន    |  ចំនួនដឹក  |  ប្រេង(L/$)")
                table_lines.append("----------------------------")

                # Sort by total trips descending
                sorted_vehicles = sorted(report.vehicles, key=lambda v: v.total_trips, reverse=True)

                for vehicle_data in sorted_vehicles:
                    # Format vehicle column (plate number only)
                    vehicle_str = vehicle_data.license_plate

                    # Format trips column as "count/loadingm³"
                    if vehicle_data.total_loading_size > 0:
                        trips_str = f"{vehicle_data.total_trips}/{vehicle_data.total_loading_size:.0f}m³"
                    else:
                        trips_str = str(vehicle_data.total_trips)

                    # Format fuel column
                    if vehicle_data.total_fuel_liters > 0:
                        fuel_str = f"{vehicle_data.total_fuel_liters:.0f}L/{vehicle_data.total_fuel_cost:.0f}$"
                    else:
                        fuel_str = "—"

                    # Build the row with pipe separators and centered alignment
                    table_lines.append(f"{vehicle_str:<10}|{trips_str:^11}| {fuel_str}")

                message_text += "<pre>" + escape('\n'.join(table_lines)) + "</pre>"
            else:
                message_text += "\n\n⚠️ គ្មានសកម្មភាពកត់ត្រាសម្រាប់ខែនេះទេ។"

            # Display report without buttons (end of session)
            if query:
                await query.edit_message_text(message_text, parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text(message_text, parse_mode=ParseMode.HTML)

        except Exception as e:
            error_message = f"❌ កំហុសក្នុងការបង្កើតរបាយការណ៍: {str(e)}"
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
            message = "❌ កំហុស: រកមិនឃើញក្រុម។ សូមចុះឈ្មោះជាមុនសិន។"
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
                "⚠️ រកមិនឃើញយានជំនិះទេ!\n\n"
                "សូមរៀបចំយានជំនិះជាមុនសិនដោយប្រើ /setup"
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

            # Show vehicle with driver name if available
            label = f"{emoji} {vehicle.license_plate}"
            if vehicle.driver_name:
                label += f" ({vehicle.driver_name})"

            keyboard.append([
                InlineKeyboardButton(label, callback_data=f"perf_vehicle_{vehicle.id}")
            ])

        keyboard.append([InlineKeyboardButton("🏠 ត្រឡប់ទៅម៉ឺនុយ", callback_data="back_to_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        message_text = "📈 របាយការណ៍ការអនុវត្តរបស់យានជំនិះ\n\nជ្រើសរើសយានជំនិះ:"

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
                f"📈 របាយការណ៍ការអនុវត្តរបស់យានជំនិះ\n\n"
                f"{emoji} {report.license_plate}\n"
            )

            if report.driver_name:
                message_text += f"👤 អ្នកបើកបរ: {report.driver_name}\n"

            # Format trips as "count/loadingm³"
            if report.month_total_loading_size > 0:
                trips_display = f"{report.month_total_trips}/{report.month_total_loading_size:.0f}m³"
            else:
                trips_display = f"{report.month_total_trips}"

            message_text += (
                f"\n📊 សង្ខេបខែនេះ:\n"
                f"• ដំណើរសរុប: {trips_display}\n"
            )

            if report.month_total_fuel > 0:
                message_text += (
                    f"• សាំងសរុប: {report.month_total_fuel}L\n"
                    f"• ចំណាយសរុប: ${report.month_total_cost:,.2f}\n"
                )

            message_text += (
                f"• មធ្យមដំណើរ/ថ្ងៃ: {report.month_avg_trips_per_day:.1f}\n"
            )

            if report.month_avg_fuel_per_trip > 0:
                message_text += (
                    f"• មធ្យមសាំង/ដំណើរ: {report.month_avg_fuel_per_trip:.1f}L\n"
                    f"• មធ្យមចំណាយ/ដំណើរ: ${report.month_avg_cost_per_trip:,.2f}\n"
                )

            # Show last 7 days breakdown
            message_text += "\n\n📅 ៧ថ្ងៃចុងក្រោយ:\n"
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
                        message_text += f"  • ដំណើរ: {trips_display}\n"
                    if day_data.fuel_liters > 0:
                        message_text += f"  • សាំង: {day_data.fuel_liters}L (${day_data.fuel_cost:,.2f})\n"

            # Display report without buttons (end of session)
            await query.edit_message_text(message_text)

        except Exception as e:
            await query.edit_message_text(f"❌ កំហុស: {str(e)}")

        return ConversationHandler.END

    # ==================== Export Handlers (Placeholders) ====================

    async def export_placeholder(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Placeholder for export functionality"""
        query = update.callback_query
        await query.answer()

        export_type = "Excel" if "excel" in query.data else "PDF"

        await query.answer(
            f"📊 មុខងារនាំចេញ {export_type} នឹងមកដល់ឆាប់ៗនេះ!",
            show_alert=True
        )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel operation"""
        await update.message.reply_text("ប្រតិបត្តិការត្រូវបានបោះបង់។")
        return ConversationHandler.END
