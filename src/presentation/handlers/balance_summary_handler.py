from telegram import Update
from telegram.ext import ContextTypes
from ...application.use_cases.get_balance_summary import GetBalanceSummaryUseCase

class BalanceSummaryHandler:
    def __init__(self, get_balance_summary_use_case: GetBalanceSummaryUseCase):
        self.get_balance_summary_use_case = get_balance_summary_use_case

    async def show_balance_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle balance summary request"""
        query = update.callback_query
        if query:
            await query.answer()

        # Get balance summary
        summary = self.get_balance_summary_use_case.execute()

        # Send the summary to the group
        message = update.effective_message
        await message.reply_text(summary, parse_mode='Markdown')
