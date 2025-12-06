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
            keyboard.append([InlineKeyboardButton("📍 ចុះឈ្មោះ", callback_data="checkin")])

        # Main menu buttons with submenus
        keyboard.append([InlineKeyboardButton("📋 ប្រតិបត្តិការប្រចាំថ្ងៃ", callback_data="menu_daily_operation")])
        keyboard.append([InlineKeyboardButton("📊 របាយការណ៍", callback_data="menu_report")])
        keyboard.append([InlineKeyboardButton("❌ បោះបង់", callback_data="cancel_menu")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        message_text = "🏠 ម៉ឺនុយមេ\n\nសូមជ្រើសរើសជម្រើសមួយ:"

        if update.callback_query:
            await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)

    async def show_daily_operation_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show daily operation submenu"""
        keyboard = [
            [InlineKeyboardButton("⛽ បន្ថែមកំណត់ត្រាសាំង", callback_data="add_fuel")],
            [InlineKeyboardButton("🚚 បន្ថែមកំណត់ត្រាដំណើរ", callback_data="add_trip")],
            [InlineKeyboardButton("🔙 ត្រឡប់ទៅម៉ឺនុយ", callback_data="back_to_menu")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = "📋 ប្រតិបត្តិការប្រចាំថ្ងៃ\n\nសូមជ្រើសរើសជម្រើសមួយ:"

        if update.callback_query:
            await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)

    async def show_report_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show report submenu"""
        keyboard = [
            [InlineKeyboardButton("📅 របាយការណ៍ប្រចាំថ្ងៃ", callback_data="report_daily")],
            [InlineKeyboardButton("📆 របាយការណ៍ប្រចាំខែ", callback_data="report_monthly")],
            [InlineKeyboardButton("📈 ការអនុវត្តរបស់យានជំនិះ", callback_data="report_vehicle_performance")],
            [InlineKeyboardButton("🔙 ត្រឡប់ទៅម៉ឺនុយ", callback_data="back_to_menu")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = "📊 របាយការណ៍\n\nសូមជ្រើសរើសជម្រើសមួយ:"

        if update.callback_query:
            await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)

    def set_check_in_enabled(self, enabled: bool):
        """Toggle check-in feature flag"""
        self.check_in_enabled = enabled
