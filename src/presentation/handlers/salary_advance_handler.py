from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from ...application.use_cases.record_salary_advance import RecordSalaryAdvanceUseCase
from ...application.dto.salary_advance_dto import SalaryAdvanceRequest
from ...infrastructure.config.settings import settings

WAITING_EMPLOYEE_NAME_ADV = 3
WAITING_ADVANCE_AMOUNT = 4
WAITING_ADVANCE_NOTE = 5

class SalaryAdvanceHandler:
    def __init__(
        self,
        record_salary_advance_use_case: RecordSalaryAdvanceUseCase
    ):
        self.record_salary_advance_use_case = record_salary_advance_use_case

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start salary advance recording (admin only)"""
        user = update.effective_user
        message = update.effective_message

        if user.id not in settings.ADMIN_IDS:
            await message.reply_text("You don't have permission to use this feature.")
            return ConversationHandler.END

        await message.reply_text("Please enter the employee's name:")
        return WAITING_EMPLOYEE_NAME_ADV

    async def get_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get employee name and ask for amount"""
        employee_name = update.message.text.strip()
        context.user_data['advance_employee_name'] = employee_name

        await update.message.reply_text(f"Enter the advance amount for {employee_name}:")
        return WAITING_ADVANCE_AMOUNT

    async def get_note(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get amount and ask for note"""
        try:
            amount = float(update.message.text.strip())
            context.user_data['advance_amount'] = amount

            await update.message.reply_text("Enter a note (optional, or type 'skip'):")
            return WAITING_ADVANCE_NOTE
        except ValueError:
            await update.message.reply_text("Invalid amount. Please enter a number:")
            return WAITING_ADVANCE_AMOUNT

    async def save(self, update: Update, context: ContextTypes.DEFAULT_TYPE, show_menu_callback):
        """Save salary advance record"""
        user = update.effective_user
        note = update.message.text.strip()

        if note.lower() == 'skip':
            note = None

        try:
            request = SalaryAdvanceRequest(
                employee_name=context.user_data['advance_employee_name'],
                amount=context.user_data['advance_amount'],
                created_by=str(user.id),
                note=note
            )
            response = self.record_salary_advance_use_case.execute(request)

            await update.message.reply_text(
                f"✅ {response.message}\n"
                f"Employee: {response.employee_name}\n"
                f"Amount: {response.amount}\n"
                f"Note: {note or 'N/A'}\n"
                f"Time: {response.timestamp}"
            )
        except ValueError as e:
            await update.message.reply_text(f"Error: {str(e)}")

        # Capture any stored employee name before clearing the context
        employee_name = context.user_data.get('employee_name')

        # Clear user data and return to the menu
        context.user_data.clear()
        await show_menu_callback(update, context, employee_name)
        return ConversationHandler.END
