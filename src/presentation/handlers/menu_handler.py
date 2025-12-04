from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

class MenuHandler:
    def __init__(self, check_in_enabled: bool = True):
        """
        Initialize menu handler

        Args:
            check_in_enabled: Feature flag for check-in button (default: True)
        """
        self.check_in_enabled = check_in_enabled

    async def show_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main menu"""
        keyboard = []

        # Check-in button (with feature flag)
        if self.check_in_enabled:
            keyboard.append([InlineKeyboardButton("📍 Check In", callback_data="checkin")])

        # Daily Operation section
        keyboard.append([
            InlineKeyboardButton("⛽ Add Fuel Record", callback_data="add_fuel"),
            InlineKeyboardButton("🚚 Add Trip Record", callback_data="add_trip")
        ])

        # Report section
        keyboard.append([
            InlineKeyboardButton("📅 Daily Report", callback_data="report_daily"),
            InlineKeyboardButton("📆 Monthly Report", callback_data="report_monthly")
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        message_text = "🏠 Main Menu\n\nChoose an option:"

        if update.callback_query:
            await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)

    def set_check_in_enabled(self, enabled: bool):
        """Toggle check-in feature flag"""
        self.check_in_enabled = enabled
