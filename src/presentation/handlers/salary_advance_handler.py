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
            await message.reply_text("អ្នកមិនមានសិទ្ធិប្រើប្រាស់មុខងារនេះទេ។")
            return ConversationHandler.END

        await message.reply_text("សូមបញ្ចូលឈ្មោះបុគ្គលិក:")
        return WAITING_EMPLOYEE_NAME_ADV

    async def get_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get employee name and ask for amount"""
        employee_name = update.message.text.strip()
        context.user_data['advance_employee_name'] = employee_name

        await update.message.reply_text(f"បញ្ចូលចំនួនទឹកប្រាក់បុរេសម្រាប់ {employee_name}:")
        return WAITING_ADVANCE_AMOUNT

    async def get_note(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get amount and ask for note"""
        try:
            amount = float(update.message.text.strip())
            context.user_data['advance_amount'] = amount

            await update.message.reply_text("បញ្ចូលកំណត់សម្គាល់ (ស្រេចចិត្ត ឬវាយ 'skip'):")
            return WAITING_ADVANCE_NOTE
        except ValueError:
            await update.message.reply_text("ចំនួនទឹកប្រាក់មិនត្រឹមត្រូវ។ សូមបញ្ចូលលេខ:")
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
                f"បុគ្គលិក: {response.employee_name}\n"
                f"ចំនួនទឹកប្រាក់: {response.amount}\n"
                f"កំណត់សម្គាល់: {note or 'គ្មាន'}\n"
                f"ពេលវេលា: {response.timestamp}"
            )
        except ValueError as e:
            await update.message.reply_text(f"កំហុស: {str(e)}")

        # Capture any stored employee name before clearing the context
        employee_name = context.user_data.get('employee_name')

        # Clear user data and return to the menu
        context.user_data.clear()
        await show_menu_callback(update, context, employee_name)
        return ConversationHandler.END
