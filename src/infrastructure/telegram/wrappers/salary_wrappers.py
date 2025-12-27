"""
Salary Advance Handler Wrappers
Contains handlers for salary advance recording
"""
from telegram import Update
from telegram.ext import ContextTypes
from ....application.use_cases.record_salary_advance import RecordSalaryAdvanceUseCase
from ....presentation.handlers.salary_advance_handler import SalaryAdvanceHandler


def create_salary_wrappers(get_repositories_func, show_menu_func):
    """
    Create salary advance handler wrappers

    Args:
        get_repositories_func: Function that returns repository tuple
        show_menu_func: Function to show the main menu

    Returns:
        Dict of wrapper functions
    """

    async def salary_advance_start_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, employee_repo, _, salary_advance_repo, _, _, _, _, _, _ = get_repositories_func()
        salary_advance_handler = SalaryAdvanceHandler(
            RecordSalaryAdvanceUseCase(salary_advance_repo, employee_repo)
        )
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_reply_markup(reply_markup=None)
            context.chat_data['menu_message_id'] = update.callback_query.message.message_id
        result = await salary_advance_handler.start(update, context)
        session.close()
        return result

    async def salary_advance_amount_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, employee_repo, _, salary_advance_repo, _, _, _, _, _, _ = get_repositories_func()
        salary_advance_handler = SalaryAdvanceHandler(
            RecordSalaryAdvanceUseCase(salary_advance_repo, employee_repo)
        )
        result = await salary_advance_handler.get_amount(update, context)
        session.close()
        return result

    async def salary_advance_note_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, employee_repo, _, salary_advance_repo, _, _, _, _, _, _ = get_repositories_func()
        salary_advance_handler = SalaryAdvanceHandler(
            RecordSalaryAdvanceUseCase(salary_advance_repo, employee_repo)
        )
        result = await salary_advance_handler.get_note(update, context)
        session.close()
        return result

    async def salary_advance_save_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, employee_repo, _, salary_advance_repo, _, _, _, _, _, _ = get_repositories_func()
        salary_advance_handler = SalaryAdvanceHandler(
            RecordSalaryAdvanceUseCase(salary_advance_repo, employee_repo)
        )
        result = await salary_advance_handler.save(update, context, show_menu_func)
        session.close()
        return result

    return {
        'salary_advance_start_wrapper': salary_advance_start_wrapper,
        'salary_advance_amount_wrapper': salary_advance_amount_wrapper,
        'salary_advance_note_wrapper': salary_advance_note_wrapper,
        'salary_advance_save_wrapper': salary_advance_save_wrapper,
    }
