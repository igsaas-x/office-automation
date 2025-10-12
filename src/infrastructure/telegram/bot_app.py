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
from ...presentation.handlers.balance_summary_handler import BalanceSummaryHandler
from ...application.use_cases.get_balance_summary import GetBalanceSummaryUseCase
from ...infrastructure.google_sheets.sheets_service import GoogleSheetsService

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
        from ...infrastructure.persistence.group_repository_impl import GroupRepository
        from ...infrastructure.persistence.employee_group_repository_impl import EmployeeGroupRepository

        return (
            EmployeeRepository(session),
            CheckInRepository(session),
            SalaryAdvanceRepository(session),
            GroupRepository(session),
            EmployeeGroupRepository(session)
        )

    async def show_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, employee_name: str = None):
        """Show main menu"""
        user = update.effective_user

        keyboard = [
            [InlineKeyboardButton("📍 Check In", callback_data="CHECK_IN")],
            [InlineKeyboardButton("📝 Request Advance", callback_data="REQUEST_ADVANCE")],
        ]

        if user.id in settings.ADMIN_IDS:
            keyboard.append([InlineKeyboardButton("💰 Record Salary Advance", callback_data="SALARY_ADVANCE")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        message = update.effective_message
        name = employee_name or user.first_name
        menu_text = (
            f"Welcome back {name}!\nPlease select an option:\n"
            "1. 📍 Check In\n"
            "2. 📝 Request Advance"
        )

        if user.id in settings.ADMIN_IDS:
            menu_text += "\n3. 💰 Record Salary Advance"

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
        await update.message.reply_text("Operation cancelled.")
        await self.show_menu(update, context)
        return ConversationHandler.END

    def _setup_handlers(self):
        """Setup all conversation handlers"""

        # Employee handlers
        async def start_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            chat = update.effective_chat
            message = update.effective_message

            employee_repo, _, _, _, _ = self._get_repositories()
            employee_handler = EmployeeHandler(
                RegisterEmployeeUseCase(employee_repo),
                GetEmployeeUseCase(employee_repo)
            )

            start_mentions_checkin = False
            if message and message.text:
                lowered = message.text.lower()
                start_mentions_checkin = lowered.startswith('/start') and 'checkin' in lowered

            pending_from_args = (
                context.args
                and len(context.args) > 0
                and context.args[0].lower() == "checkin"
            )

            if start_mentions_checkin or pending_from_args:
                context.user_data['pending_checkin_command'] = True

            # Create a wrapper for show_menu that skips if checkin is pending or in groups
            async def show_menu_or_skip(update, context, employee_name=None):
                if context.user_data.get('pending_checkin_command'):
                    return
                if chat.type in ['group', 'supergroup']:
                    return
                await self.show_menu(update, context, employee_name)

            result = await employee_handler.start(update, context, show_menu_or_skip)

            pending_from_flag = context.user_data.get('pending_checkin_command', False)

            if result == ConversationHandler.END and (pending_from_args or pending_from_flag):
                context.user_data.pop('pending_checkin_command', None)
                await checkin_command(update, context)

            return result

        async def menu_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            chat = update.effective_chat
            message = update.effective_message
            user = update.effective_user

            # /menu only works in group chats
            if chat.type == 'private':
                if message:
                    await message.reply_text(
                        "In private chat, please use /start instead of /menu."
                    )
                return

            # Check if employee is registered
            employee_repo, _, _, _, _ = self._get_repositories()
            employee = GetEmployeeUseCase(employee_repo).execute_by_telegram_id(str(user.id))

            if not employee:
                await message.reply_text(
                    "Please register first by starting a private chat with the bot and using /start."
                )
                return

            # Show menu in group
            keyboard = [
                [InlineKeyboardButton("📍 Check In", callback_data="CHECK_IN")],
                [InlineKeyboardButton("💰 Balance Summary", callback_data="BALANCE_SUMMARY")],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            menu_text = f"Hello {employee.name}!\nPlease select an option:"

            await message.reply_text(menu_text, reply_markup=reply_markup)

        async def register_group_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            from ...application.use_cases.register_group import RegisterGroupUseCase

            chat = update.effective_chat
            message = update.effective_message

            # Only works in group chats
            if chat.type not in ['group', 'supergroup']:
                if message:
                    await message.reply_text("This command only works in group chats.")
                return

            # Register the group
            _, _, _, group_repo, _ = self._get_repositories()
            register_group_use_case = RegisterGroupUseCase(group_repo)

            group = register_group_use_case.execute(
                chat_id=str(chat.id),
                name=chat.title or "Unknown Group"
            )

            await message.reply_text(
                f"✅ Group '{group.name}' has been registered successfully!\n"
                f"You can now use the Balance Summary feature in this group."
            )

        async def register_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            employee_repo, _, _, _, _ = self._get_repositories()
            employee_handler = EmployeeHandler(
                RegisterEmployeeUseCase(employee_repo),
                GetEmployeeUseCase(employee_repo)
            )

            message = update.effective_message
            chat = update.effective_chat

            if message and message.text and 'checkin' in message.text.lower():
                context.user_data['pending_checkin_command'] = True

            # In groups, don't show menu
            if chat.type in ['group', 'supergroup']:
                async def skip_menu(update, context, employee_name=None):
                    pass
                result = await employee_handler.register(update, context, skip_menu)
            else:
                result = await employee_handler.register(update, context, self.show_menu)

            if context.user_data.get('pending_checkin_command'):
                context.user_data.pop('pending_checkin_command', None)
                await checkin_command(update, context)

            return result

        async def register_command_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            employee_repo, _, _, _, _ = self._get_repositories()
            employee_handler = EmployeeHandler(
                RegisterEmployeeUseCase(employee_repo),
                GetEmployeeUseCase(employee_repo)
            )

            # In groups, don't show menu after registration
            async def skip_menu(update, context, employee_name=None):
                pass

            return await employee_handler.start(update, context, skip_menu)

        async def checkin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            chat = update.effective_chat
            message = update.effective_message

            if chat.type != 'private':
                if message:
                    await message.reply_text(
                        "Please use /checkin in a private chat with the bot."
                    )
                return

            employee_repo, _, _, _, _ = self._get_repositories()
            employee = GetEmployeeUseCase(employee_repo).execute_by_telegram_id(
                str(update.effective_user.id)
            )

            if not employee:
                await message.reply_text("Please register first using /start in a private chat.")
                return

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📍 Start Check-In", callback_data="CHECK_IN")]
            ])

            await message.reply_text(
                "Ready to check in? Tap the button below to share your location.",
                reply_markup=keyboard
            )

        # Check-in handlers
        async def check_in_request_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            from ...application.use_cases.register_group import RegisterGroupUseCase
            from ...application.use_cases.add_employee_to_group import AddEmployeeToGroupUseCase

            employee_repo, check_in_repo, _, group_repo, employee_group_repo = self._get_repositories()
            check_in_handler = CheckInHandler(
                RecordCheckInUseCase(check_in_repo, employee_repo, group_repo),
                GetEmployeeUseCase(employee_repo),
                RegisterGroupUseCase(group_repo),
                AddEmployeeToGroupUseCase(employee_group_repo, employee_repo, group_repo)
            )
            if update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.edit_message_reply_markup(reply_markup=None)
                context.chat_data['menu_message_id'] = update.callback_query.message.message_id
            return await check_in_handler.request_location(update, context)

        async def check_in_process_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            from ...application.use_cases.register_group import RegisterGroupUseCase
            from ...application.use_cases.add_employee_to_group import AddEmployeeToGroupUseCase

            employee_repo, check_in_repo, _, group_repo, employee_group_repo = self._get_repositories()
            check_in_handler = CheckInHandler(
                RecordCheckInUseCase(check_in_repo, employee_repo, group_repo),
                GetEmployeeUseCase(employee_repo),
                RegisterGroupUseCase(group_repo),
                AddEmployeeToGroupUseCase(employee_group_repo, employee_repo, group_repo)
            )

            # Don't show menu in private chat after check-in
            async def skip_menu(update, context, employee_name=None):
                pass

            return await check_in_handler.process_check_in(update, context, skip_menu)

        async def request_advance_placeholder(update: Update, context: ContextTypes.DEFAULT_TYPE):
            query = update.callback_query
            if query:
                await query.answer()
                await query.edit_message_reply_markup(reply_markup=None)
                context.chat_data['menu_message_id'] = query.message.message_id

            message = update.effective_message
            await message.reply_text("The request advance feature is coming soon.")
            await self.show_menu(update, context)

        # Salary advance handlers
        async def salary_advance_start_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            employee_repo, _, salary_advance_repo, _, _ = self._get_repositories()
            salary_advance_handler = SalaryAdvanceHandler(
                RecordSalaryAdvanceUseCase(salary_advance_repo, employee_repo)
            )
            if update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.edit_message_reply_markup(reply_markup=None)
                context.chat_data['menu_message_id'] = update.callback_query.message.message_id
            return await salary_advance_handler.start(update, context)

        async def salary_advance_amount_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            employee_repo, _, salary_advance_repo, _, _ = self._get_repositories()
            salary_advance_handler = SalaryAdvanceHandler(
                RecordSalaryAdvanceUseCase(salary_advance_repo, employee_repo)
            )
            return await salary_advance_handler.get_amount(update, context)

        async def salary_advance_note_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            employee_repo, _, salary_advance_repo, _, _ = self._get_repositories()
            salary_advance_handler = SalaryAdvanceHandler(
                RecordSalaryAdvanceUseCase(salary_advance_repo, employee_repo)
            )
            return await salary_advance_handler.get_note(update, context)

        async def salary_advance_save_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            employee_repo, _, salary_advance_repo, _, _ = self._get_repositories()
            salary_advance_handler = SalaryAdvanceHandler(
                RecordSalaryAdvanceUseCase(salary_advance_repo, employee_repo)
            )
            return await salary_advance_handler.save(update, context, self.show_menu)

        # Balance summary handler
        async def balance_summary_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            sheets_service = GoogleSheetsService()
            balance_summary_handler = BalanceSummaryHandler(
                GetBalanceSummaryUseCase(sheets_service)
            )
            await balance_summary_handler.show_balance_summary(update, context)

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

        # Check-in conversation handler
        check_in_conv = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(check_in_request_wrapper, pattern="^CHECK_IN$"),
                MessageHandler(filters.Regex("^📍 Check In$"), check_in_request_wrapper),
            ],
            states={
                WAITING_LOCATION: [MessageHandler(filters.LOCATION, check_in_process_wrapper)],
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

        # Add handlers
        self.app.add_handler(CommandHandler("menu", menu_wrapper))
        self.app.add_handler(CommandHandler("checkin", checkin_command))
        self.app.add_handler(CommandHandler("register_group", register_group_wrapper))
        self.app.add_handler(registration_conv)
        self.app.add_handler(check_in_conv)
        self.app.add_handler(CallbackQueryHandler(request_advance_placeholder, pattern="^REQUEST_ADVANCE$"))
        self.app.add_handler(request_advance_handler)
        self.app.add_handler(salary_advance_conv)
        self.app.add_handler(CallbackQueryHandler(balance_summary_wrapper, pattern="^BALANCE_SUMMARY$"))

    def run(self):
        """Start the bot"""
        print("Bot is running...")
        self.app.run_polling()
