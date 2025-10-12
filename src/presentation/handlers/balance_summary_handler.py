from telegram import Update
from telegram.ext import ContextTypes
from ...application.use_cases.get_balance_summary import GetBalanceSummaryUseCase

class BalanceSummaryHandler:
    def __init__(self, get_balance_summary_use_case: GetBalanceSummaryUseCase):
        self.get_balance_summary_use_case = get_balance_summary_use_case

    async def show_balance_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle balance summary request"""
        query = update.callback_query

        try:
            # Get balance summary
            summary = self.get_balance_summary_use_case.execute()

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
            error_message = f"❌ Failed to retrieve balance summary.\n\nError: {str(e)}"

            if query:
                await query.answer()
                await query.edit_message_text(error_message)
            else:
                message = update.effective_message
                await message.reply_text(error_message)
