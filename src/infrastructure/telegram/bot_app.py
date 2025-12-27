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
from ...presentation.handlers.employee_handler import WAITING_EMPLOYEE_NAME
from ...presentation.handlers.registration_handler import WAITING_FOR_BUSINESS_NAME
from ...presentation.handlers.salary_advance_handler import (
    WAITING_EMPLOYEE_NAME_ADV,
    WAITING_ADVANCE_AMOUNT,
    WAITING_ADVANCE_NOTE
)
from ...presentation.handlers.setup_handler import (
    SETUP_MENU,
    SETUP_VEHICLE_PLATE,
    SETUP_VEHICLE_DRIVER,
    SETUP_DRIVER_NAME,
    SETUP_DRIVER_ROLE,
    SETUP_DRIVER_PHONE,
    SETUP_DRIVER_VEHICLE
)
from ...presentation.handlers.vehicle_operations_handler import (
    SELECT_VEHICLE_FOR_TRIP,
    ENTER_TRIP_COUNT,
    ENTER_TOTAL_LOADING_SIZE,
    SELECT_VEHICLE_FOR_FUEL,
    ENTER_FUEL_LITERS,
    ENTER_FUEL_COST,
    UPLOAD_FUEL_RECEIPT
)
from ...presentation.handlers.report_handler import SELECT_VEHICLE_FOR_PERFORMANCE
from ...infrastructure.persistence.vehicle_repository_impl import VehicleRepository
from ...infrastructure.persistence.trip_repository_impl import TripRepository
from ...infrastructure.persistence.fuel_record_repository_impl import FuelRecordRepository

# Import wrapper modules
from .wrappers.employee_wrappers import create_employee_wrappers
from .wrappers.salary_wrappers import create_salary_wrappers
from .wrappers.registration_wrappers import create_registration_wrappers
from .wrappers.menu_wrappers import create_menu_wrappers
from .wrappers.setup_wrappers import create_setup_wrappers
from .wrappers.vehicle_operations_wrappers import create_vehicle_operations_wrappers
from .wrappers.report_wrappers import create_report_wrappers


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

    def _get_repositories_for_handlers(self):
        """Get repository tuple unpacked specifically for handlers"""
        (session, employee_repo, check_in_repo, salary_advance_repo,
         group_repo, employee_group_repo, vehicle_repo, trip_repo,
         fuel_repo, telegram_user_repo) = self._get_repositories()

        return {
            'session': session,
            'employee_repo': employee_repo,
            'check_in_repo': check_in_repo,
            'salary_advance_repo': salary_advance_repo,
            'group_repo': group_repo,
            'employee_group_repo': employee_group_repo,
            'vehicle_repo': vehicle_repo,
            'trip_repo': trip_repo,
            'fuel_repo': fuel_repo,
            'telegram_user_repo': telegram_user_repo
        }

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
        # Create wrapper functions from modules
        employee_wrappers = create_employee_wrappers(self._get_repositories, self.show_menu)
        salary_wrappers = create_salary_wrappers(self._get_repositories, self.show_menu)
        registration_wrappers = create_registration_wrappers(self._get_repositories_for_handlers)
        menu_wrappers = create_menu_wrappers(self._get_repositories_for_handlers)
        setup_wrappers = create_setup_wrappers(self._get_repositories)
        vehicle_ops_wrappers = create_vehicle_operations_wrappers(self._get_repositories)
        report_wrappers = create_report_wrappers(self._get_repositories)

        # Extract wrappers for easier reference
        start_wrapper = employee_wrappers['start_wrapper']
        register_wrapper = employee_wrappers['register_wrapper']
        register_command_wrapper = employee_wrappers['register_command_wrapper']
        request_advance_placeholder = employee_wrappers['request_advance_placeholder']

        salary_advance_start_wrapper = salary_wrappers['salary_advance_start_wrapper']
        salary_advance_amount_wrapper = salary_wrappers['salary_advance_amount_wrapper']
        salary_advance_note_wrapper = salary_wrappers['salary_advance_note_wrapper']
        salary_advance_save_wrapper = salary_wrappers['salary_advance_save_wrapper']

        register_group_start_wrapper = registration_wrappers['register_group_start_wrapper']
        register_group_receive_name_wrapper = registration_wrappers['register_group_receive_name_wrapper']

        menu_wrapper = menu_wrappers['menu_wrapper']
        report_command_wrapper = menu_wrappers['report_command_wrapper']
        menu_reports_callback_wrapper = menu_wrappers['menu_reports_callback_wrapper']
        report_daily_callback_wrapper = menu_wrappers['report_daily_callback_wrapper']
        report_monthly_callback_wrapper = menu_wrappers['report_monthly_callback_wrapper']
        back_to_main_menu_wrapper = menu_wrappers['back_to_main_menu_wrapper']
        back_to_menu_wrapper = menu_wrappers['back_to_menu_wrapper']
        show_daily_operation_menu_wrapper = menu_wrappers['show_daily_operation_menu_wrapper']
        show_report_menu_wrapper = menu_wrappers['show_report_menu_wrapper']
        cancel_menu_wrapper = menu_wrappers['cancel_menu_wrapper']

        setup_menu_wrapper = setup_wrappers['setup_menu_wrapper']
        setup_vehicle_start_wrapper = setup_wrappers['setup_vehicle_start_wrapper']
        setup_vehicle_plate_wrapper = setup_wrappers['setup_vehicle_plate_wrapper']
        setup_vehicle_driver_wrapper = setup_wrappers['setup_vehicle_driver_wrapper']
        setup_driver_start_wrapper = setup_wrappers['setup_driver_start_wrapper']
        setup_driver_name_wrapper = setup_wrappers['setup_driver_name_wrapper']
        setup_driver_role_wrapper = setup_wrappers['setup_driver_role_wrapper']
        setup_driver_phone_wrapper = setup_wrappers['setup_driver_phone_wrapper']
        setup_driver_vehicle_wrapper = setup_wrappers['setup_driver_vehicle_wrapper']
        setup_list_vehicles_wrapper = setup_wrappers['setup_list_vehicles_wrapper']
        setup_list_drivers_wrapper = setup_wrappers['setup_list_drivers_wrapper']
        setup_delete_vehicle_wrapper = setup_wrappers['setup_delete_vehicle_wrapper']
        setup_delete_driver_wrapper = setup_wrappers['setup_delete_driver_wrapper']
        setup_back_to_menu_wrapper = setup_wrappers['setup_back_to_menu_wrapper']
        cancel_setup_wrapper = setup_wrappers['cancel_setup_wrapper']

        start_trip_recording_wrapper = vehicle_ops_wrappers['start_trip_recording_wrapper']
        select_trip_vehicle_wrapper = vehicle_ops_wrappers['select_trip_vehicle_wrapper']
        receive_trip_count_wrapper = vehicle_ops_wrappers['receive_trip_count_wrapper']
        receive_total_loading_size_wrapper = vehicle_ops_wrappers['receive_total_loading_size_wrapper']
        start_fuel_recording_wrapper = vehicle_ops_wrappers['start_fuel_recording_wrapper']
        select_fuel_vehicle_wrapper = vehicle_ops_wrappers['select_fuel_vehicle_wrapper']
        receive_fuel_liters_wrapper = vehicle_ops_wrappers['receive_fuel_liters_wrapper']
        receive_fuel_cost_wrapper = vehicle_ops_wrappers['receive_fuel_cost_wrapper']
        complete_fuel_record_wrapper = vehicle_ops_wrappers['complete_fuel_record_wrapper']

        show_daily_report_wrapper = report_wrappers['show_daily_report_wrapper']
        show_monthly_report_wrapper = report_wrappers['show_monthly_report_wrapper']
        start_vehicle_performance_wrapper = report_wrappers['start_vehicle_performance_wrapper']
        show_vehicle_performance_wrapper = report_wrappers['show_vehicle_performance_wrapper']
        export_placeholder_wrapper = report_wrappers['export_placeholder_wrapper']

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

        # Group registration conversation handler
        group_registration_conv = ConversationHandler(
            entry_points=[
                CommandHandler("register", register_group_start_wrapper),
            ],
            states={
                WAITING_FOR_BUSINESS_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, register_group_receive_name_wrapper)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        # Add handlers
        self.app.add_handler(CommandHandler("menu", menu_wrapper))
        self.app.add_handler(CommandHandler("report", report_command_wrapper))
        self.app.add_handler(group_registration_conv)
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

        # Add report callback handlers
        self.app.add_handler(CallbackQueryHandler(menu_reports_callback_wrapper, pattern="^menu_reports_"))
        self.app.add_handler(CallbackQueryHandler(report_daily_callback_wrapper, pattern="^report_daily_"))
        self.app.add_handler(CallbackQueryHandler(report_monthly_callback_wrapper, pattern="^report_monthly_"))

        # Add navigation handlers
        self.app.add_handler(CallbackQueryHandler(back_to_main_menu_wrapper, pattern="^back_to_main_menu_"))

        # Add cancel handlers
        self.app.add_handler(CallbackQueryHandler(cancel_menu_wrapper, pattern="^cancel_menu$"))

    def run(self):
        """Start the bot"""
        print("Check-in Bot is running...")
        self.app.run_polling()
