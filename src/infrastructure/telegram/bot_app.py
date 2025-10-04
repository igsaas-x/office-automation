from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters, ContextTypes
from ...infrastructure.config.settings import settings
from ...infrastructure.persistence.database import database
from ...infrastructure.persistence.employee_repository_impl import EmployeeRepository
from ...infrastructure.persistence.check_in_repository_impl import CheckInRepository
from ...infrastructure.persistence.salary_advance_repository_impl import SalaryAdvanceRepository
from ...application.use_cases.register_employee import RegisterEmployeeUseCase
from ...application.use_cases.get_employee import GetEmployeeUseCase
from ...application.use_cases.record_check_in import RecordCheckInUseCase
from ...application.use_cases.record_salary_advance import RecordSalaryAdvanceUseCase
from ...presentation.handlers.employee_handler import EmployeeHandler, WAITING_EMPLOYEE_NAME
from ...presentation.handlers.check_in_handler import CheckInHandler, WAITING_LOCATION
from ...presentation.handlers.salary_advance_handler import (
    SalaryAdvanceHandler,
    WAITING_EMPLOYEE_NAME_ADV,
    WAITING_ADVANCE_AMOUNT,
    WAITING_ADVANCE_NOTE
)

class BotApplication:
    def __init__(self):
        # Initialize database
        database.create_tables()

        # Create application
        self.app = Application.builder().token(settings.BOT_TOKEN).build()

        # Setup handlers
        self._setup_handlers()

    def _get_repositories(self):
        """Get repository instances with a new session"""
        session = database.get_session()
        return (
            EmployeeRepository(session),
            CheckInRepository(session),
            SalaryAdvanceRepository(session)
        )

    async def show_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, employee_name: str = None):
        """Show main menu"""
        user = update.effective_user

        keyboard = [
            [KeyboardButton("📍 Check In")],
        ]

        # Add admin options
        if user.id in settings.ADMIN_IDS:
            keyboard.append([KeyboardButton("💰 Record Salary Advance")])

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        name = employee_name or user.first_name
        await update.message.reply_text(
            f"Welcome back {name}!\nPlease select an option:",
            reply_markup=reply_markup
        )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel conversation"""
        await update.message.reply_text("Operation cancelled.")
        await self.show_menu(update, context)
        return ConversationHandler.END

    def _setup_handlers(self):
        """Setup all conversation handlers"""

        # Employee handlers
        async def start_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            employee_repo, _, _ = self._get_repositories()
            employee_handler = EmployeeHandler(
                RegisterEmployeeUseCase(employee_repo),
                GetEmployeeUseCase(employee_repo)
            )
            return await employee_handler.start(update, context, self.show_menu)

        async def register_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            employee_repo, _, _ = self._get_repositories()
            employee_handler = EmployeeHandler(
                RegisterEmployeeUseCase(employee_repo),
                GetEmployeeUseCase(employee_repo)
            )
            return await employee_handler.register(update, context, self.show_menu)

        # Check-in handlers
        async def check_in_request_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            employee_repo, check_in_repo, _ = self._get_repositories()
            check_in_handler = CheckInHandler(
                RecordCheckInUseCase(check_in_repo, employee_repo),
                GetEmployeeUseCase(employee_repo)
            )
            return await check_in_handler.request_location(update, context)

        async def check_in_process_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            employee_repo, check_in_repo, _ = self._get_repositories()
            check_in_handler = CheckInHandler(
                RecordCheckInUseCase(check_in_repo, employee_repo),
                GetEmployeeUseCase(employee_repo)
            )
            return await check_in_handler.process_check_in(update, context, self.show_menu)

        # Salary advance handlers
        async def salary_advance_start_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            employee_repo, _, salary_advance_repo = self._get_repositories()
            salary_advance_handler = SalaryAdvanceHandler(
                RecordSalaryAdvanceUseCase(salary_advance_repo, employee_repo)
            )
            return await salary_advance_handler.start(update, context)

        async def salary_advance_amount_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            employee_repo, _, salary_advance_repo = self._get_repositories()
            salary_advance_handler = SalaryAdvanceHandler(
                RecordSalaryAdvanceUseCase(salary_advance_repo, employee_repo)
            )
            return await salary_advance_handler.get_amount(update, context)

        async def salary_advance_note_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            employee_repo, _, salary_advance_repo = self._get_repositories()
            salary_advance_handler = SalaryAdvanceHandler(
                RecordSalaryAdvanceUseCase(salary_advance_repo, employee_repo)
            )
            return await salary_advance_handler.get_note(update, context)

        async def salary_advance_save_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            employee_repo, _, salary_advance_repo = self._get_repositories()
            salary_advance_handler = SalaryAdvanceHandler(
                RecordSalaryAdvanceUseCase(salary_advance_repo, employee_repo)
            )
            return await salary_advance_handler.save(update, context, self.show_menu)

        # Registration conversation handler
        registration_conv = ConversationHandler(
            entry_points=[CommandHandler("start", start_wrapper)],
            states={
                WAITING_EMPLOYEE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_wrapper)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        # Check-in conversation handler
        check_in_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^📍 Check In$"), check_in_request_wrapper)],
            states={
                WAITING_LOCATION: [MessageHandler(filters.LOCATION, check_in_process_wrapper)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        # Salary advance conversation handler
        salary_advance_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^💰 Record Salary Advance$"), salary_advance_start_wrapper)],
            states={
                WAITING_EMPLOYEE_NAME_ADV: [MessageHandler(filters.TEXT & ~filters.COMMAND, salary_advance_amount_wrapper)],
                WAITING_ADVANCE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, salary_advance_note_wrapper)],
                WAITING_ADVANCE_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, salary_advance_save_wrapper)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        # Add handlers
        self.app.add_handler(registration_conv)
        self.app.add_handler(check_in_conv)
        self.app.add_handler(salary_advance_conv)

    def run(self):
        """Start the bot"""
        print("Bot is running...")
        self.app.run_polling()
