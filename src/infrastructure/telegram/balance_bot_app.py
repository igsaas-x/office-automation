from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from ...infrastructure.config.settings import settings
from ...infrastructure.google_sheets.sheets_service import GoogleSheetsService
from ...application.use_cases.get_balance_summary import GetBalanceSummaryUseCase
from ...presentation.handlers.balance_summary_handler import BalanceSummaryHandler


class BalanceBotApplication:
    """Separate bot dedicated to balance summary functionality"""

    def __init__(self):
        # Create application with balance bot token
        self.app = Application.builder().token(settings.BALANCE_BOT_TOKEN).build()

        # Setup handlers
        self._setup_handlers()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        message = update.effective_message
        await message.reply_text(
            "👋 Welcome to the Balance Summary Bot!\n\n"
            "Use /balance to get the current month's balance summary."
        )

    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command"""
        sheets_service = GoogleSheetsService()
        balance_summary_handler = BalanceSummaryHandler(
            GetBalanceSummaryUseCase(sheets_service)
        )
        await balance_summary_handler.show_balance_summary(update, context)

    async def balance_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle balance button callback"""
        sheets_service = GoogleSheetsService()
        balance_summary_handler = BalanceSummaryHandler(
            GetBalanceSummaryUseCase(sheets_service)
        )
        await balance_summary_handler.show_balance_summary(update, context)

    def _setup_handlers(self):
        """Setup all handlers for the balance bot"""
        # Command handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("balance", self.balance_command))

        # Callback query handler for button clicks
        self.app.add_handler(CallbackQueryHandler(self.balance_callback, pattern="^BALANCE_SUMMARY$"))

    def run(self):
        """Start the bot"""
        print("Balance Bot is running...")
        self.app.run_polling()
