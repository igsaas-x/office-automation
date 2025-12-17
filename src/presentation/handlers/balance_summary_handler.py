from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from ...application.use_cases.get_balance_summary import GetBalanceSummaryUseCase

class BalanceSummaryHandler:
    # List of months for selection
    MONTHS = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    def __init__(self, get_balance_summary_use_case: GetBalanceSummaryUseCase):
        self.get_balance_summary_use_case = get_balance_summary_use_case

    async def show_month_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   callback_prefix: str = "BALANCE_MONTH", title: str = "📅 ជ្រើសរើសខែដើម្បីមើលសង្ខេបសមតុល្យ:"):
        """Show month selection keyboard

        Args:
            update: Telegram update
            context: Telegram context
            callback_prefix: Prefix for callback data (e.g., "BALANCE_MONTH" or "MUSIC_SCHOOL_MONTH")
            title: Message title to display
        """
        # Create inline keyboard with month buttons (3 columns)
        keyboard = []
        row = []
        for i, month in enumerate(self.MONTHS):
            row.append(InlineKeyboardButton(month, callback_data=f"{callback_prefix}_{month}"))
            if (i + 1) % 3 == 0:
                keyboard.append(row)
                row = []

        # Add any remaining buttons
        if row:
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard)

        message = update.effective_message
        await message.reply_text(title, reply_markup=reply_markup)

    async def show_balance_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   month: str = None, sheet_id: str = None, sheet_url: str = None):
        """Handle balance summary request for a specific month

        Args:
            update: Telegram update
            context: Telegram context
            month: Optional month name
            sheet_id: Optional Google Sheets ID
            sheet_url: Optional Google Sheets URL for the link
        """
        query = update.callback_query

        try:
            # Get balance summary for the specified month (or current if None)
            summary = self.get_balance_summary_use_case.execute(month, sheet_id, sheet_url)

            # If it's a callback query, edit the existing message
            if query:
                await query.answer()
                await query.edit_message_text(summary, parse_mode='HTML')
            else:
                # Otherwise, send a new message
                message = update.effective_message
                await message.reply_text(summary, parse_mode='HTML')
        except Exception as e:
            # If there's an error, send without formatting
            error_message = f"❌ បរាជ័យក្នុងការទាញយកសង្ខេបសមតុល្យ។\n\nកំហុស: {str(e)}"

            if query:
                await query.answer()
                await query.edit_message_text(error_message)
            else:
                message = update.effective_message
                await message.reply_text(error_message)
