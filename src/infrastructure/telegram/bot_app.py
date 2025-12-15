from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from telegram.error import TelegramError
from ...infrastructure.config.settings import settings
from ...infrastructure.persistence.database import database
from ...infrastructure.persistence.employee_repository_impl import EmployeeRepository
from ...infrastructure.persistence.check_in_repository_impl import CheckInRepository
from ...infrastructure.persistence.salary_advance_repository_impl import SalaryAdvanceRepository
from ...application.use_cases.register_employee import RegisterEmployeeUseCase
from ...application.use_cases.get_employee import GetEmployeeUseCase
from ...application.use_cases.record_salary_advance import RecordSalaryAdvanceUseCase
from ...presentation.handlers.employee_handler import EmployeeHandler, WAITING_EMPLOYEE_NAME
from ...presentation.handlers.salary_advance_handler import (
    SalaryAdvanceHandler,
    WAITING_EMPLOYEE_NAME_ADV,
    WAITING_ADVANCE_AMOUNT,
    WAITING_ADVANCE_NOTE
)
from ...presentation.handlers.setup_handler import (
    SetupHandler,
    SETUP_MENU,
    SETUP_VEHICLE_PLATE,
    SETUP_VEHICLE_DRIVER,
    SETUP_DRIVER_NAME,
    SETUP_DRIVER_ROLE,
    SETUP_DRIVER_PHONE,
    SETUP_DRIVER_VEHICLE
)
from ...presentation.handlers.menu_handler import MenuHandler
from ...presentation.handlers.vehicle_operations_handler import (
    VehicleOperationsHandler,
    SELECT_VEHICLE_FOR_TRIP,
    ENTER_TRIP_COUNT,
    ENTER_TOTAL_LOADING_SIZE,
    SELECT_VEHICLE_FOR_FUEL,
    ENTER_FUEL_LITERS,
    ENTER_FUEL_COST,
    UPLOAD_FUEL_RECEIPT
)
from ...presentation.handlers.report_handler import (
    ReportHandler,
    SELECT_VEHICLE_FOR_PERFORMANCE
)
from ...infrastructure.persistence.vehicle_repository_impl import VehicleRepository
from ...infrastructure.persistence.trip_repository_impl import TripRepository
from ...infrastructure.persistence.fuel_record_repository_impl import FuelRecordRepository
from ...application.use_cases.register_vehicle import RegisterVehicleUseCase
from ...application.use_cases.register_group import RegisterGroupUseCase
from ...application.use_cases.delete_vehicle import DeleteVehicleUseCase
from ...application.use_cases.record_trip import RecordTripUseCase
from ...application.use_cases.record_fuel import RecordFuelUseCase
from ...application.use_cases.get_daily_report import GetDailyReportUseCase
from ...application.use_cases.get_monthly_report import GetMonthlyReportUseCase
from ...application.use_cases.get_vehicle_performance import GetVehiclePerformanceUseCase

class BotApplication:
    def __init__(self):
        # Initialize database
        database.create_tables()

        # Create application with check-in bot token (or fallback to BOT_TOKEN for backward compatibility)
        bot_token = settings.CHECKIN_BOT_TOKEN or settings.BOT_TOKEN
        self.app = Application.builder().token(bot_token).build()

        # Setup handlers
        self._setup_handlers()

    def _get_repositories(self):
        """Get repository instances with a new session"""
        session = database.get_session()
        from ...infrastructure.persistence.group_repository_impl import GroupRepository
        from ...infrastructure.persistence.employee_group_repository_impl import EmployeeGroupRepository
        from ...infrastructure.persistence.telegram_user_repository_impl import TelegramUserRepository

        return (
            session,
            EmployeeRepository(session),
            CheckInRepository(session),
            SalaryAdvanceRepository(session),
            GroupRepository(session),
            EmployeeGroupRepository(session),
            VehicleRepository(session),
            TripRepository(session),
            FuelRecordRepository(session),
            TelegramUserRepository(session)
        )

    async def show_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, employee_name: str = None):
        """Show main menu"""
        user = update.effective_user

        keyboard = [
            [InlineKeyboardButton("📍 ចុះឈ្មោះ", url="https://t.me/OALocal_bot/checkin")],
            [InlineKeyboardButton("📝 ស្នើសុំបុរេ", callback_data="REQUEST_ADVANCE")],
        ]

        if user.id in settings.ADMIN_IDS:
            keyboard.append([InlineKeyboardButton("💰 កត់ត្រាបុរេប្រាក់ខែ", callback_data="SALARY_ADVANCE")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        message = update.effective_message
        name = employee_name or user.first_name
        menu_text = (
            f"សូមស្វាគមន៍ {name}!\nសូមជ្រើសរើសជម្រើសមួយ:\n"
            "1. 📍 ចុះឈ្មោះ\n"
            "2. 📝 ស្នើសុំបុរេ"
        )

        if user.id in settings.ADMIN_IDS:
            menu_text += "\n3. 💰 កត់ត្រាបុរេប្រាក់ខែ"

        chat_data = context.chat_data
        query = update.callback_query

        if query:
            try:
                await query.edit_message_text(menu_text, reply_markup=reply_markup)
            except TelegramError as error:
                if "message is not modified" in str(error).lower():
                    try:
                        await query.edit_message_reply_markup(reply_markup=reply_markup)
                    except TelegramError as markup_error:
                        if "message is not modified" not in str(markup_error).lower():
                            raise
                else:
                    raise

            chat_data['menu_message_id'] = query.message.message_id
            return

        menu_message_id = chat_data.get('menu_message_id')
        chat_id = message.chat_id

        if menu_message_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=menu_message_id,
                    text=menu_text,
                    reply_markup=reply_markup
                )
                chat_data['menu_message_id'] = menu_message_id
                return
            except TelegramError as error:
                error_text = str(error).lower()
                if "message is not modified" in error_text:
                    try:
                        await context.bot.edit_message_reply_markup(
                            chat_id=chat_id,
                            message_id=menu_message_id,
                            reply_markup=reply_markup
                        )
                        chat_data['menu_message_id'] = menu_message_id
                        return
                    except TelegramError as markup_error:
                        if "message is not modified" in str(markup_error).lower():
                            return
                        raise
                # If the original menu message is gone, fall back to sending a new one
                chat_data.pop('menu_message_id', None)

        sent_message = await message.reply_text(menu_text, reply_markup=reply_markup)
        chat_data['menu_message_id'] = sent_message.message_id

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel conversation"""
        await update.message.reply_text("ប្រតិបត្តិការត្រូវបានបោះបង់។")
        await self.show_menu(update, context)
        return ConversationHandler.END

    def _setup_handlers(self):
        """Setup all conversation handlers"""

        # Employee handlers
        async def start_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            chat = update.effective_chat

            session, employee_repo, _, _, _, _, _, _, _ = self._get_repositories()
            employee_handler = EmployeeHandler(
                RegisterEmployeeUseCase(employee_repo),
                GetEmployeeUseCase(employee_repo)
            )

            # Create a wrapper for show_menu that skips in groups
            async def show_menu_or_skip(update, context, employee_name=None):
                if chat.type in ['group', 'supergroup']:
                    session.close()
                    return
                await self.show_menu(update, context, employee_name)
                session.close()

            return await employee_handler.start(update, context, show_menu_or_skip)

        async def menu_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            chat = update.effective_chat
            message = update.effective_message
            user = update.effective_user

            # /menu only works in group chats
            if chat.type == 'private':
                if message:
                    await message.reply_text(
                        "នៅក្នុងការសន្ទនាឯកជន សូមប្រើ /start ជំនួសឱ្យ /menu។"
                    )
                return

            # Check if employee is registered
            session, employee_repo, _, _, _, _, _, _, _ = self._get_repositories()
            employee = GetEmployeeUseCase(employee_repo).execute_by_telegram_id(str(user.id))
            session.close()

            if not employee:
                await message.reply_text(
                    "សូមចុះឈ្មោះជាមុនសិនដោយចាប់ផ្តើមការសន្ទនាឯកជនជាមួយបូត និងប្រើ /start។"
                )
                return

            # Show menu using MenuHandler (with check-in disabled)
            menu_handler = MenuHandler(check_in_enabled=False)
            await menu_handler.show_menu(update, context)

        async def register_group_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            chat = update.effective_chat
            message = update.effective_message
            user = update.effective_user

            # Only works in group chats
            if chat.type not in ['group', 'supergroup']:
                if message:
                    await message.reply_text("ពាក្យបញ្ជានេះដំណើរការតែនៅក្នុងការសន្ទនាក្រុមប៉ុណ្ណោះ។")
                return

            # Register the group with owner information
            session, _, _, _, group_repo, _, _, _, _, user_repo = self._get_repositories()
            register_group_use_case = RegisterGroupUseCase(group_repo, user_repo)

            group = register_group_use_case.execute(
                chat_id=str(chat.id),
                name=chat.title or "ក្រុមមិនស្គាល់",
                created_by_telegram_id=str(user.id) if user else None,
                created_by_username=user.username if user else None,
                created_by_first_name=user.first_name if user else None,
                created_by_last_name=user.last_name if user else None
            )
            session.close()

            await message.reply_text(
                f"✅ ក្រុម '{group.name}' ត្រូវបានចុះឈ្មោះដោយជោគជ័យ!"
            )

        async def register_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, employee_repo, _, _, _, _, _, _, _ = self._get_repositories()
            employee_handler = EmployeeHandler(
                RegisterEmployeeUseCase(employee_repo),
                GetEmployeeUseCase(employee_repo)
            )

            chat = update.effective_chat

            # In groups, don't show menu
            if chat.type in ['group', 'supergroup']:
                async def skip_menu(update, context, employee_name=None):
                    session.close()
                result = await employee_handler.register(update, context, skip_menu)
                return result
            else:
                result = await employee_handler.register(update, context, self.show_menu)
                session.close()
                return result

        async def register_command_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, employee_repo, _, _, _, _, _, _, _ = self._get_repositories()
            employee_handler = EmployeeHandler(
                RegisterEmployeeUseCase(employee_repo),
                GetEmployeeUseCase(employee_repo)
            )

            # In groups, don't show menu after registration
            async def skip_menu(update, context, employee_name=None):
                session.close()

            return await employee_handler.start(update, context, skip_menu)

        async def request_advance_placeholder(update: Update, context: ContextTypes.DEFAULT_TYPE):
            query = update.callback_query
            if query:
                await query.answer()
                await query.edit_message_reply_markup(reply_markup=None)
                context.chat_data['menu_message_id'] = query.message.message_id

            message = update.effective_message
            await message.reply_text("មុខងារស្នើសុំបុរេនឹងមកដល់ឆាប់ៗនេះ។")
            await self.show_menu(update, context)

        # Salary advance handlers
        async def salary_advance_start_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, employee_repo, _, salary_advance_repo, _, _, _, _, _ = self._get_repositories()
            salary_advance_handler = SalaryAdvanceHandler(
                RecordSalaryAdvanceUseCase(salary_advance_repo, employee_repo)
            )
            if update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.edit_message_reply_markup(reply_markup=None)
                context.chat_data['menu_message_id'] = update.callback_query.message.message_id
            result = await salary_advance_handler.start(update, context)
            session.close()
            return result

        async def salary_advance_amount_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, employee_repo, _, salary_advance_repo, _, _, _, _, _ = self._get_repositories()
            salary_advance_handler = SalaryAdvanceHandler(
                RecordSalaryAdvanceUseCase(salary_advance_repo, employee_repo)
            )
            result = await salary_advance_handler.get_amount(update, context)
            session.close()
            return result

        async def salary_advance_note_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, employee_repo, _, salary_advance_repo, _, _, _, _, _ = self._get_repositories()
            salary_advance_handler = SalaryAdvanceHandler(
                RecordSalaryAdvanceUseCase(salary_advance_repo, employee_repo)
            )
            result = await salary_advance_handler.get_note(update, context)
            session.close()
            return result

        async def salary_advance_save_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, employee_repo, _, salary_advance_repo, _, _, _, _, _ = self._get_repositories()
            salary_advance_handler = SalaryAdvanceHandler(
                RecordSalaryAdvanceUseCase(salary_advance_repo, employee_repo)
            )
            result = await salary_advance_handler.save(update, context, self.show_menu)
            session.close()
            return result

        # ==================== Vehicle Logistics Handlers ====================

        # Setup handlers
        def build_setup_handler(include_group: bool = False):
            session, _, _, _, group_repo, _, vehicle_repo, trip_repo, fuel_repo = self._get_repositories()
            setup_handler = SetupHandler(
                RegisterVehicleUseCase(vehicle_repo),
                None,  # RegisterDriverUseCase - driver functionality removed
                RegisterGroupUseCase(group_repo) if include_group else None,
                vehicle_repo,
                None,  # driver_repo - driver functionality removed
                DeleteVehicleUseCase(vehicle_repo, trip_repo, fuel_repo),
                None  # DeleteDriverUseCase - driver functionality removed
            )
            return session, setup_handler

        async def setup_menu_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, setup_handler = build_setup_handler(include_group=True)
            result = await setup_handler.setup_menu(update, context)
            session.close()
            return result

        async def setup_vehicle_start_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, setup_handler = build_setup_handler()
            result = await setup_handler.start_vehicle_setup(update, context)
            session.close()
            return result

        async def setup_vehicle_plate_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, setup_handler = build_setup_handler()
            result = await setup_handler.receive_vehicle_plate(update, context)
            session.close()
            return result

        async def setup_vehicle_driver_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, setup_handler = build_setup_handler()
            result = await setup_handler.receive_vehicle_driver_name(update, context)
            session.close()
            return result

        async def setup_driver_start_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, setup_handler = build_setup_handler()
            result = await setup_handler.start_driver_setup(update, context)
            session.close()
            return result

        async def setup_driver_name_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, setup_handler = build_setup_handler()
            result = await setup_handler.receive_driver_name(update, context)
            session.close()
            return result

        async def setup_driver_role_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, setup_handler = build_setup_handler()
            result = await setup_handler.receive_driver_role(update, context)
            session.close()
            return result

        async def setup_driver_phone_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, setup_handler = build_setup_handler()
            result = await setup_handler.receive_driver_phone(update, context)
            session.close()
            return result

        async def setup_driver_vehicle_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, setup_handler = build_setup_handler()
            result = await setup_handler.receive_driver_vehicle(update, context)
            session.close()
            return result

        async def setup_list_vehicles_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, setup_handler = build_setup_handler()
            result = await setup_handler.list_vehicles(update, context)
            session.close()
            return result

        async def setup_list_drivers_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, setup_handler = build_setup_handler()
            result = await setup_handler.list_drivers(update, context)
            session.close()
            return result

        async def setup_delete_vehicle_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, setup_handler = build_setup_handler()
            result = await setup_handler.delete_vehicle(update, context)
            session.close()
            return result

        async def setup_delete_driver_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, setup_handler = build_setup_handler()
            result = await setup_handler.delete_driver(update, context)
            session.close()
            return result

        async def setup_back_to_menu_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, setup_handler = build_setup_handler(include_group=True)
            result = await setup_handler.back_to_setup_menu(update, context)
            session.close()
            return result

        # Vehicle operations handlers
        async def start_trip_recording_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo = self._get_repositories()
            vehicle_ops_handler = VehicleOperationsHandler(
                RecordTripUseCase(trip_repo, vehicle_repo),
                RecordFuelUseCase(None, vehicle_repo),  # fuel_repo passed later
                vehicle_repo
            )
            result = await vehicle_ops_handler.start_trip_recording(update, context)
            session.close()
            return result

        async def select_trip_vehicle_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo = self._get_repositories()
            vehicle_ops_handler = VehicleOperationsHandler(
                RecordTripUseCase(trip_repo, vehicle_repo),
                RecordFuelUseCase(None, vehicle_repo),
                vehicle_repo
            )
            result = await vehicle_ops_handler.select_trip_vehicle(update, context)
            session.close()
            return result

        async def receive_trip_count_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo = self._get_repositories()
            vehicle_ops_handler = VehicleOperationsHandler(
                RecordTripUseCase(trip_repo, vehicle_repo),
                RecordFuelUseCase(None, vehicle_repo),
                vehicle_repo
            )
            result = await vehicle_ops_handler.receive_trip_count(update, context)
            session.close()
            return result

        async def receive_total_loading_size_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo = self._get_repositories()
            vehicle_ops_handler = VehicleOperationsHandler(
                RecordTripUseCase(trip_repo, vehicle_repo),
                RecordFuelUseCase(None, vehicle_repo),
                vehicle_repo
            )
            result = await vehicle_ops_handler.receive_total_loading_size(update, context)
            session.close()
            return result

        async def start_fuel_recording_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo = self._get_repositories()
            vehicle_ops_handler = VehicleOperationsHandler(
                RecordTripUseCase(None, vehicle_repo),
                RecordFuelUseCase(fuel_repo, vehicle_repo),
                vehicle_repo
            )
            result = await vehicle_ops_handler.start_fuel_recording(update, context)
            session.close()
            return result

        async def select_fuel_vehicle_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo = self._get_repositories()
            vehicle_ops_handler = VehicleOperationsHandler(
                RecordTripUseCase(None, vehicle_repo),
                RecordFuelUseCase(fuel_repo, vehicle_repo),
                vehicle_repo
            )
            result = await vehicle_ops_handler.select_fuel_vehicle(update, context)
            session.close()
            return result

        async def receive_fuel_liters_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo = self._get_repositories()
            vehicle_ops_handler = VehicleOperationsHandler(
                RecordTripUseCase(None, vehicle_repo),
                RecordFuelUseCase(fuel_repo, vehicle_repo),
                vehicle_repo
            )
            result = await vehicle_ops_handler.receive_fuel_liters(update, context)
            session.close()
            return result

        async def receive_fuel_cost_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo = self._get_repositories()
            vehicle_ops_handler = VehicleOperationsHandler(
                RecordTripUseCase(None, vehicle_repo),
                RecordFuelUseCase(fuel_repo, vehicle_repo),
                vehicle_repo
            )
            result = await vehicle_ops_handler.receive_fuel_cost(update, context)
            session.close()
            return result

        async def complete_fuel_record_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo = self._get_repositories()
            vehicle_ops_handler = VehicleOperationsHandler(
                RecordTripUseCase(None, vehicle_repo),
                RecordFuelUseCase(fuel_repo, vehicle_repo),
                vehicle_repo
            )
            result = await vehicle_ops_handler.complete_fuel_record(update, context)
            session.close()
            return result

        # Report handlers
        async def show_daily_report_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo = self._get_repositories()
            report_handler = ReportHandler(
                GetDailyReportUseCase(vehicle_repo, None, trip_repo, fuel_repo),
                GetMonthlyReportUseCase(vehicle_repo, None, trip_repo, fuel_repo),
                GetVehiclePerformanceUseCase(vehicle_repo, None, trip_repo, fuel_repo),
                vehicle_repo, None
            )
            await report_handler.show_daily_report(update, context)
            session.close()

        async def show_monthly_report_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo = self._get_repositories()
            report_handler = ReportHandler(
                GetDailyReportUseCase(vehicle_repo, None, trip_repo, fuel_repo),
                GetMonthlyReportUseCase(vehicle_repo, None, trip_repo, fuel_repo),
                GetVehiclePerformanceUseCase(vehicle_repo, None, trip_repo, fuel_repo),
                vehicle_repo, None
            )
            await report_handler.show_monthly_report(update, context)
            session.close()

        async def start_vehicle_performance_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo = self._get_repositories()
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
            session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo = self._get_repositories()
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
            session, _, _, _, _, _, vehicle_repo, trip_repo, fuel_repo = self._get_repositories()
            report_handler = ReportHandler(
                GetDailyReportUseCase(vehicle_repo, None, trip_repo, fuel_repo),
                GetMonthlyReportUseCase(vehicle_repo, None, trip_repo, fuel_repo),
                GetVehiclePerformanceUseCase(vehicle_repo, None, trip_repo, fuel_repo),
                vehicle_repo, None
            )
            await report_handler.export_placeholder(update, context)
            session.close()

        async def back_to_menu_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle back to menu button"""
            menu_handler = MenuHandler(check_in_enabled=False)
            await menu_handler.show_menu(update, context)

        async def show_daily_operation_menu_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle daily operation menu button"""
            menu_handler = MenuHandler(check_in_enabled=False)
            await menu_handler.show_daily_operation_menu(update, context)
            return ConversationHandler.END

        async def show_report_menu_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle report menu button"""
            menu_handler = MenuHandler(check_in_enabled=False)
            await menu_handler.show_report_menu(update, context)

        async def cancel_menu_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle cancel button from main menu"""
            query = update.callback_query
            await query.answer()
            await query.edit_message_text("❌ ម៉ឺនុយត្រូវបានបោះបង់។")

        async def cancel_setup_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle cancel button from setup menu"""
            query = update.callback_query
            await query.answer()
            await query.edit_message_text("❌ ការរៀបចំត្រូវបានបោះបង់។")
            return ConversationHandler.END

        # Registration conversation handler
        registration_conv = ConversationHandler(
            entry_points=[
                CommandHandler("start", start_wrapper),
                CommandHandler("register", register_command_wrapper)
            ],
            states={
                WAITING_EMPLOYEE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_wrapper)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        # Placeholder handler for request advance button
        request_advance_handler = MessageHandler(
            filters.Regex("^📝 Request Advance$"),
            request_advance_placeholder
        )

        # Salary advance conversation handler
        salary_advance_conv = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(salary_advance_start_wrapper, pattern="^SALARY_ADVANCE$"),
                MessageHandler(filters.Regex("^💰 Record Salary Advance$"), salary_advance_start_wrapper),
            ],
            states={
                WAITING_EMPLOYEE_NAME_ADV: [MessageHandler(filters.TEXT & ~filters.COMMAND, salary_advance_amount_wrapper)],
                WAITING_ADVANCE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, salary_advance_note_wrapper)],
                WAITING_ADVANCE_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, salary_advance_save_wrapper)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        # Setup conversation handler
        setup_conv = ConversationHandler(
            entry_points=[
                CommandHandler("setup", setup_menu_wrapper),
            ],
            states={
                SETUP_MENU: [
                    CallbackQueryHandler(setup_vehicle_start_wrapper, pattern="^setup_vehicle$"),
                    CallbackQueryHandler(setup_driver_start_wrapper, pattern="^setup_driver$"),
                    CallbackQueryHandler(setup_list_vehicles_wrapper, pattern="^list_vehicles$"),
                    CallbackQueryHandler(setup_list_drivers_wrapper, pattern="^list_drivers$"),
                    CallbackQueryHandler(setup_delete_vehicle_wrapper, pattern="^delete_vehicle_"),
                    CallbackQueryHandler(setup_delete_driver_wrapper, pattern="^delete_driver_"),
                    CallbackQueryHandler(setup_back_to_menu_wrapper, pattern="^back_to_setup$"),
                    CallbackQueryHandler(cancel_setup_wrapper, pattern="^cancel_setup$"),
                ],
                SETUP_VEHICLE_PLATE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, setup_vehicle_plate_wrapper)
                ],
                SETUP_VEHICLE_DRIVER: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, setup_vehicle_driver_wrapper),
                    CallbackQueryHandler(setup_vehicle_driver_wrapper, pattern="^vehicle_skip_driver$")
                ],
                SETUP_DRIVER_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, setup_driver_name_wrapper)
                ],
                SETUP_DRIVER_ROLE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, setup_driver_role_wrapper)
                ],
                SETUP_DRIVER_PHONE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, setup_driver_phone_wrapper)
                ],
                SETUP_DRIVER_VEHICLE: [
                    CallbackQueryHandler(setup_driver_vehicle_wrapper, pattern="^assign_vehicle_")
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        # Trip recording conversation handler
        trip_conv = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(start_trip_recording_wrapper, pattern="^add_trip$"),
            ],
            states={
                SELECT_VEHICLE_FOR_TRIP: [
                    CallbackQueryHandler(select_trip_vehicle_wrapper, pattern="^trip_vehicle_"),
                    CallbackQueryHandler(show_daily_operation_menu_wrapper, pattern="^menu_daily_operation$")
                ],
                ENTER_TRIP_COUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_trip_count_wrapper)
                ],
                ENTER_TOTAL_LOADING_SIZE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_total_loading_size_wrapper)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        # Fuel recording conversation handler
        fuel_conv = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(start_fuel_recording_wrapper, pattern="^add_fuel$"),
            ],
            states={
                SELECT_VEHICLE_FOR_FUEL: [
                    CallbackQueryHandler(select_fuel_vehicle_wrapper, pattern="^fuel_vehicle_"),
                    CallbackQueryHandler(show_daily_operation_menu_wrapper, pattern="^menu_daily_operation$")
                ],
                ENTER_FUEL_LITERS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_fuel_liters_wrapper)
                ],
                ENTER_FUEL_COST: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_fuel_cost_wrapper)
                ],
                UPLOAD_FUEL_RECEIPT: [
                    MessageHandler(filters.PHOTO, complete_fuel_record_wrapper),
                    CallbackQueryHandler(complete_fuel_record_wrapper, pattern="^fuel_skip_photo$"),
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        # Vehicle performance conversation handler
        vehicle_performance_conv = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(start_vehicle_performance_wrapper, pattern="^report_vehicle_performance$"),
            ],
            states={
                SELECT_VEHICLE_FOR_PERFORMANCE: [
                    CallbackQueryHandler(show_vehicle_performance_wrapper, pattern="^perf_vehicle_")
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        # Add handlers
        self.app.add_handler(CommandHandler("menu", menu_wrapper))
        self.app.add_handler(CommandHandler("register_group", register_group_wrapper))
        self.app.add_handler(registration_conv)
        self.app.add_handler(CallbackQueryHandler(request_advance_placeholder, pattern="^REQUEST_ADVANCE$"))
        self.app.add_handler(request_advance_handler)
        self.app.add_handler(salary_advance_conv)

        # Add vehicle logistics handlers
        self.app.add_handler(setup_conv)
        self.app.add_handler(trip_conv)
        self.app.add_handler(fuel_conv)
        self.app.add_handler(vehicle_performance_conv)

        # Add report callback handlers
        self.app.add_handler(CallbackQueryHandler(show_daily_report_wrapper, pattern="^report_daily$"))
        self.app.add_handler(CallbackQueryHandler(show_monthly_report_wrapper, pattern="^report_monthly$"))

        # Add export placeholder handlers
        self.app.add_handler(CallbackQueryHandler(export_placeholder_wrapper, pattern="^export_.*"))

        # Add back to menu handler
        self.app.add_handler(CallbackQueryHandler(back_to_menu_wrapper, pattern="^back_to_menu$"))

        # Add submenu handlers
        self.app.add_handler(CallbackQueryHandler(show_daily_operation_menu_wrapper, pattern="^menu_daily_operation$"))
        self.app.add_handler(CallbackQueryHandler(show_report_menu_wrapper, pattern="^menu_report$"))

        # Add cancel handlers
        self.app.add_handler(CallbackQueryHandler(cancel_menu_wrapper, pattern="^cancel_menu$"))

    def run(self):
        """Start the bot"""
        print("Check-in Bot is running...")
        self.app.run_polling()
