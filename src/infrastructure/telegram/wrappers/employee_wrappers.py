"""
Employee Registration Handler Wrappers
Contains handlers for employee registration and related functionality
"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from ....application.use_cases.register_employee import RegisterEmployeeUseCase
from ....application.use_cases.get_employee import GetEmployeeUseCase
from ....presentation.handlers.employee_handler import EmployeeHandler


def create_employee_wrappers(get_repositories_func, show_menu_func):
    """
    Create employee-related handler wrappers

    Args:
        get_repositories_func: Function that returns repository tuple
        show_menu_func: Function to show the main menu

    Returns:
        Dict of wrapper functions
    """

    async def start_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat

        session, employee_repo, _, _, _, _, _, _, _, _ = get_repositories_func()
        employee_handler = EmployeeHandler(
            RegisterEmployeeUseCase(employee_repo),
            GetEmployeeUseCase(employee_repo)
        )

        # Create a wrapper for show_menu that skips in groups
        async def show_menu_or_skip(update, context, employee_name=None):
            if chat.type in ['group', 'supergroup']:
                session.close()
                return
            await show_menu_func(update, context, employee_name)
            session.close()

        return await employee_handler.start(update, context, show_menu_or_skip)

    async def register_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, employee_repo, _, _, _, _, _, _, _, _ = get_repositories_func()
        employee_handler = EmployeeHandler(
            RegisterEmployeeUseCase(employee_repo),
            GetEmployeeUseCase(employee_repo)
        )

        chat = update.effective_chat

        # In groups, don't show menu
        if chat.type in ['group', 'supergroup']:
            async def skip_menu(update, context, employee_name=None):
                session.close()
            result = await employee_handler.register(update, context, skip_menu)
            return result
        else:
            result = await employee_handler.register(update, context, show_menu_func)
            session.close()
            return result

    async def register_command_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, employee_repo, _, _, _, _, _, _, _, _ = get_repositories_func()
        employee_handler = EmployeeHandler(
            RegisterEmployeeUseCase(employee_repo),
            GetEmployeeUseCase(employee_repo)
        )

        # In groups, don't show menu after registration
        async def skip_menu(update, context, employee_name=None):
            session.close()

        return await employee_handler.start(update, context, skip_menu)

    async def request_advance_placeholder(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if query:
            await query.answer()
            await query.edit_message_reply_markup(reply_markup=None)
            context.chat_data['menu_message_id'] = query.message.message_id

        message = update.effective_message
        await message.reply_text("មុខងារស្នើសុំបុរេនឹងមកដល់ឆាប់ៗនេះ។")
        await show_menu_func(update, context)

    return {
        'start_wrapper': start_wrapper,
        'register_wrapper': register_wrapper,
        'register_command_wrapper': register_command_wrapper,
        'request_advance_placeholder': request_advance_placeholder,
    }
