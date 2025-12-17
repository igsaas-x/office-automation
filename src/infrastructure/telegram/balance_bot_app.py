from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from ...infrastructure.config.settings import settings
from ...infrastructure.google_sheets.sheets_service import GoogleSheetsService
from ...application.use_cases.get_balance_summary import GetBalanceSummaryUseCase
from ...presentation.handlers.balance_summary_handler import BalanceSummaryHandler
from ...infrastructure.llm.expense_parser_client import ExpenseParserClient


class BalanceBotApplication:
    """Separate bot dedicated to balance summary functionality"""

    def __init__(self):
        # Create application with balance bot token
        self.app = Application.builder().token(settings.BALANCE_BOT_TOKEN).build()

        self.sheets_service = GoogleSheetsService()
        self.expense_parser = ExpenseParserClient()
        self.balance_summary_handler = BalanceSummaryHandler(
            GetBalanceSummaryUseCase(self.sheets_service),
            sheets_service=self.sheets_service,
            expense_parser=self.expense_parser,
        )

        # Setup handlers
        self._setup_handlers()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        message = update.effective_message
        await message.reply_text(
            "👋 Welcome to the Balance Summary Bot!\n\n"
            "Available commands:\n"
            "• /balance - View office balance summary\n"
            "• /balance_music_school - View music school balance summary"
        )

    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command - show month selection"""
        await self.balance_summary_handler.show_month_selection(update, context)

    async def balance_music_school_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance_music_school command - show month selection for music school"""
        await self.balance_summary_handler.show_month_selection(
            update,
            context,
            callback_prefix="MUSIC_SCHOOL_MONTH",
            title="🎵 Select a month to view Music School balance summary:"
        )

    async def balance_month_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle month selection callback"""
        query = update.callback_query
        # Extract month from callback_data (format: "BALANCE_MONTH_{month}")
        month = query.data.replace("BALANCE_MONTH_", "")

        await self.balance_summary_handler.show_balance_summary(update, context, month=month)

    async def music_school_month_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle music school month selection callback"""
        query = update.callback_query
        # Extract month from callback_data (format: "MUSIC_SCHOOL_MONTH_{month}")
        month = query.data.replace("MUSIC_SCHOOL_MONTH_", "")

        await self.balance_summary_handler.show_balance_summary(
            update,
            context,
            month=month,
            sheet_id=settings.MUSIC_SCHOOL_SHEET_ID,
            sheet_url="https://docs.google.com/spreadsheets/d/1vSjYtvKxQPdFUrowO2kd7bXoU9bwd_Tpf06Twdw_4YU/edit?gid=0#gid=0"
        )

    async def balance_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle balance button callback - show month selection"""
        await self.balance_summary_handler.show_month_selection(update, context)

    async def group_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle group text for expense logging."""
        await self.balance_summary_handler.handle_group_expense(update, context)

    def _setup_handlers(self):
        """Setup all handlers for the balance bot"""
        # Command handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("balance", self.balance_command))
        self.app.add_handler(CommandHandler("balance_music_school", self.balance_music_school_command))

        # Callback query handlers
        self.app.add_handler(CallbackQueryHandler(self.balance_month_callback, pattern="^BALANCE_MONTH_"))
        self.app.add_handler(CallbackQueryHandler(self.music_school_month_callback, pattern="^MUSIC_SCHOOL_MONTH_"))
        self.app.add_handler(CallbackQueryHandler(self.balance_callback, pattern="^BALANCE_SUMMARY$"))

        # Group message listener for expenses
        self.app.add_handler(
            MessageHandler(
                filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND,
                self.group_message_handler
            )
        )

    def run(self):
        """Start the bot"""
        print("Balance Bot is running...")
        self.app.run_polling()
