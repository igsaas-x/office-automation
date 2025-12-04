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

        # Main menu buttons with submenus
        keyboard.append([InlineKeyboardButton("📋 Daily Operation", callback_data="menu_daily_operation")])
        keyboard.append([InlineKeyboardButton("📊 Report", callback_data="menu_report")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        message_text = "🏠 Main Menu\n\nChoose an option:"

        if update.callback_query:
            await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)

    async def show_daily_operation_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show daily operation submenu"""
        keyboard = [
            [InlineKeyboardButton("⛽ Add Fuel Record", callback_data="add_fuel")],
            [InlineKeyboardButton("🚚 Add Trip Record", callback_data="add_trip")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = "📋 Daily Operation\n\nChoose an option:"

        if update.callback_query:
            await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)

    async def show_report_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show report submenu"""
        keyboard = [
            [InlineKeyboardButton("📅 Daily Report", callback_data="report_daily")],
            [InlineKeyboardButton("📆 Monthly Report", callback_data="report_monthly")],
            [InlineKeyboardButton("📈 Vehicle Performance", callback_data="report_vehicle_performance")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = "📊 Report\n\nChoose an option:"

        if update.callback_query:
            await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)

    def set_check_in_enabled(self, enabled: bool):
        """Toggle check-in feature flag"""
        self.check_in_enabled = enabled
