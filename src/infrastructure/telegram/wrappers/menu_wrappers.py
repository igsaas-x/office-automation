"""
Menu and Report Handler Wrappers
Contains handlers for /menu command and report functionality
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from ....presentation.handlers.menu_handler import MenuHandler
from ....presentation.handlers.checkin_report_handler import CheckInReportHandler
from ....application.use_cases.get_employee import GetEmployeeUseCase


def create_menu_wrappers(get_repositories_func):
    """
    Create menu-related handler wrappers

    Args:
        get_repositories_func: Function that returns repository dict

    Returns:
        Dict of wrapper functions
    """

    async def menu_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /menu command"""
        chat = update.effective_chat
        message = update.effective_message
        user = update.effective_user

        # Get repositories
        repos = get_repositories_func()
        session = repos['session']
        employee_repo = repos['employee_repo']
        group_repo = repos['group_repo']

        try:
            # For private chats, show vehicle logistics menu
            if chat.type == 'private':
                # Check if employee is registered
                employee = GetEmployeeUseCase(employee_repo).execute_by_telegram_id(str(user.id))

                if not employee:
                    await message.reply_text(
                        "សូមចុះឈ្មោះជាមុនសិនដោយចាប់ផ្តើមការសន្ទនាឯកជនជាមួយបូត និងប្រើ /start។"
                    )
                    return

                # Show vehicle logistics menu (with check-in disabled)
                menu_handler = MenuHandler(check_in_enabled=False, group_repository=None)
                await menu_handler.show_menu(update, context)
                return

            # For group chats, show menu with deep links
            menu_handler = MenuHandler(check_in_enabled=True, group_repository=group_repo)
            await menu_handler.show_menu(update, context)

        finally:
            session.close()

    async def report_command_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /report command"""
        repos = get_repositories_func()
        session = repos['session']
        group_repo = repos['group_repo']
        check_in_repo = repos['check_in_repo']
        employee_repo = repos['employee_repo']

        try:
            report_handler = CheckInReportHandler(group_repo, check_in_repo, employee_repo)
            await report_handler.show_report_menu(update, context)
        finally:
            session.close()

    async def menu_reports_callback_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Reports button from menu - show report selection"""
        query = update.callback_query
        await query.answer()

        # Extract group_id from callback_data: "menu_reports_{group_id}"
        group_id = int(query.data.split('_')[-1])

        repos = get_repositories_func()
        session = repos['session']
        group_repo = repos['group_repo']

        try:
            # Get group
            group = group_repo.find_by_id(group_id)
            if not group:
                await query.edit_message_text("⚠️ Group not found.")
                return

            # Show report type selection
            keyboard = [
                [InlineKeyboardButton("📅 របាយការណ៍ថ្ងៃនេះ Today's Report", callback_data=f"report_daily_{group.id}")],
                [InlineKeyboardButton("📆 របាយការណ៍ខែនេះ Monthly Report", callback_data=f"report_monthly_{group.id}")],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data=f"back_to_main_menu_{group_id}")],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                f"<b>{group.business_name or group.name}</b>\n\n"
                f"📊 <b>របាយការណ៍ការចុះឈ្មោះ Check-In Reports</b>\n\n"
                f"សូមជ្រើសរើសប្រភេទរបាយការណ៍:\n"
                f"Please select report type:",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        finally:
            session.close()

    async def report_daily_callback_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle daily report callback"""
        query = update.callback_query
        group_id = int(query.data.split('_')[-1])

        repos = get_repositories_func()
        session = repos['session']
        group_repo = repos['group_repo']
        check_in_repo = repos['check_in_repo']
        employee_repo = repos['employee_repo']

        try:
            report_handler = CheckInReportHandler(group_repo, check_in_repo, employee_repo)
            await report_handler.show_daily_report(update, context, group_id)
        finally:
            session.close()

    async def report_monthly_callback_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle monthly report callback"""
        query = update.callback_query
        group_id = int(query.data.split('_')[-1])

        repos = get_repositories_func()
        session = repos['session']
        group_repo = repos['group_repo']
        check_in_repo = repos['check_in_repo']
        employee_repo = repos['employee_repo']

        try:
            report_handler = CheckInReportHandler(group_repo, check_in_repo, employee_repo)
            await report_handler.show_monthly_report(update, context, group_id)
        finally:
            session.close()

    async def back_to_main_menu_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle back to main menu button"""
        query = update.callback_query
        await query.answer()

        group_id = int(query.data.split('_')[-1])

        repos = get_repositories_func()
        session = repos['session']
        group_repo = repos['group_repo']

        try:
            # Get group
            group = group_repo.find_by_id(group_id)
            if not group:
                await query.edit_message_text("⚠️ Group not found.")
                return

            # Recreate the main menu
            group_id_param = abs(int(group.chat_id))

            checkin_link = f"https://t.me/office_automation_bot/checkin?startapp=group_{group_id_param}"
            employee_link = f"https://t.me/office_automation_bot/employees?startapp=group_{group_id_param}"

            keyboard = [
                [InlineKeyboardButton("✅ Check In", url=checkin_link)],
                [InlineKeyboardButton("👥 Employees", url=employee_link)],
                [InlineKeyboardButton("📊 Reports", callback_data=f"menu_reports_{group.id}")],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            business_name = group.business_name or group.name
            message_text = (
                f"<b>{business_name}</b>\n\n"
                f"Select an action below:\n"
                f"• <b>Check In</b> - Record your attendance with photo & location\n"
                f"• <b>Employees</b> - View and manage employee information\n"
                f"• <b>Reports</b> - View attendance and payment history"
            )

            await query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode='HTML')
        finally:
            session.close()

    async def back_to_menu_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle back to menu button (for vehicle logistics)"""
        repos = get_repositories_func()
        session = repos['session']
        group_repo = repos['group_repo']

        try:
            menu_handler = MenuHandler(check_in_enabled=False, group_repository=group_repo)
            await menu_handler.show_menu(update, context)
        finally:
            session.close()

    async def show_daily_operation_menu_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle daily operation menu button"""
        repos = get_repositories_func()
        session = repos['session']
        group_repo = repos['group_repo']

        try:
            menu_handler = MenuHandler(check_in_enabled=False, group_repository=group_repo)
            await menu_handler.show_daily_operation_menu(update, context)
            from telegram.ext import ConversationHandler
            return ConversationHandler.END
        finally:
            session.close()

    async def show_report_menu_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle report menu button"""
        repos = get_repositories_func()
        session = repos['session']
        group_repo = repos['group_repo']

        try:
            menu_handler = MenuHandler(check_in_enabled=False, group_repository=group_repo)
            await menu_handler.show_report_menu(update, context)
        finally:
            session.close()

    async def cancel_menu_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle cancel button from main menu"""
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("❌ ម៉ឺនុយត្រូវបានបោះបង់។")

    return {
        'menu_wrapper': menu_wrapper,
        'report_command_wrapper': report_command_wrapper,
        'menu_reports_callback_wrapper': menu_reports_callback_wrapper,
        'report_daily_callback_wrapper': report_daily_callback_wrapper,
        'report_monthly_callback_wrapper': report_monthly_callback_wrapper,
        'back_to_main_menu_wrapper': back_to_main_menu_wrapper,
        'back_to_menu_wrapper': back_to_menu_wrapper,
        'show_daily_operation_menu_wrapper': show_daily_operation_menu_wrapper,
        'show_report_menu_wrapper': show_report_menu_wrapper,
        'cancel_menu_wrapper': cancel_menu_wrapper,
    }
