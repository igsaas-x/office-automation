from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from ...domain.repositories.group_repository import IGroupRepository

class MenuHandler:
    def __init__(self, check_in_enabled: bool = True, group_repository: IGroupRepository = None):
        """
        Initialize menu handler

        Args:
            check_in_enabled: Feature flag for check-in button (default: True)
            group_repository: Repository for group operations (required for deep links)
        """
        self.check_in_enabled = check_in_enabled
        self.group_repository = group_repository

    async def show_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Show main menu with deep link buttons (for group chats)
        or regular menu (for private chats)
        """
        chat = update.effective_chat
        message = update.effective_message

        # For group chats, show menu with deep links
        if chat.type in ['group', 'supergroup']:
            await self._show_group_menu(update, context, chat)
            return

        # For private chats, show regular menu (vehicle logistics)
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
            await message.reply_text(message_text, reply_markup=reply_markup)

    async def _show_group_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat):
        """
        Show menu with deep link buttons for group chats
        Each button opens miniapp with group context
        """
        message = update.effective_message

        # Check if group is registered
        if not self.group_repository:
            await message.reply_text(
                "⚠️ ប្រព័ន្ធមិនត្រូវបានកំណត់រចនាសម្ព័ន្ធត្រឹមត្រូវទេ។\n\n"
                "System is not configured properly."
            )
            return

        group = self.group_repository.find_by_chat_id(str(chat.id))

        if not group:
            await message.reply_text(
                "⚠️ ក្រុមនេះមិនទាន់ចុះឈ្មោះទេ។\n\n"
                "សូមសួរអ្នកគ្រប់គ្រង ឱ្យរត់ពាក្យបញ្ជា /register ជាមុនសិន។\n\n"
                "---\n\n"
                "⚠️ This group is not registered.\n\n"
                "Please ask an admin to run /register first to set up this business."
            )
            return

        # Generate deep links with group context
        group_id_param = abs(int(chat.id))  # Remove negative sign for URL

        checkin_link = f"https://t.me/office_automation_bot/checkin?startapp=group_{group_id_param}"
        balance_link = f"https://t.me/office_automation_bot/balance?startapp=group_{group_id_param}"

        # Create inline keyboard with action buttons
        keyboard = [
            [InlineKeyboardButton("✅ Check In", url=checkin_link)],
            [InlineKeyboardButton("💰 View Balance", url=balance_link)],
            [InlineKeyboardButton("📊 Reports", callback_data=f"menu_reports_{group.id}")],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        business_name = group.business_name or group.name
        message_text = (
            f"<b>{business_name}</b>\n\n"
            f"Select an action below:\n"
            f"• <b>Check In</b> - Record your attendance with photo & location\n"
            f"• <b>View Balance</b> - See your salary balance and advances\n"
            f"• <b>My Reports</b> - View your attendance and payment history"
        )

        await message.reply_text(message_text, reply_markup=reply_markup, parse_mode='HTML')

    async def show_daily_operation_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show daily operation submenu"""
        keyboard = [
            [InlineKeyboardButton("⛽ កត់ត្រាសាំង", callback_data="add_fuel")],
            [InlineKeyboardButton("🚚 កត់ត្រាចំនួនដឹក", callback_data="add_trip")],
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
            # [InlineKeyboardButton("📈 ការអនុវត្តរបស់យានជំនិះ", callback_data="report_vehicle_performance")],
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
