from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from ...application.use_cases.register_employee import RegisterEmployeeUseCase
from ...application.use_cases.get_employee import GetEmployeeUseCase
from ...application.dto.employee_dto import RegisterEmployeeRequest

WAITING_EMPLOYEE_NAME = 2

class EmployeeHandler:
    def __init__(
        self,
        register_employee_use_case: RegisterEmployeeUseCase,
        get_employee_use_case: GetEmployeeUseCase
    ):
        self.register_employee_use_case = register_employee_use_case
        self.get_employee_use_case = get_employee_use_case

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE, show_menu_callback):
        """Start command handler"""
        user = update.effective_user

        # Check if employee exists
        employee = self.get_employee_use_case.execute_by_telegram_id(str(user.id))

        if not employee:
            await update.message.reply_text(
                f"ស្វាគមន៍ {user.first_name}! សូមបញ្ចូលឈ្មោះពេញរបស់អ្នកដើម្បីចុះឈ្មោះ:"
            )
            return WAITING_EMPLOYEE_NAME

        # Show menu
        await show_menu_callback(update, context, employee.name)
        return ConversationHandler.END

    async def register(self, update: Update, context: ContextTypes.DEFAULT_TYPE, show_menu_callback):
        """Register new employee"""
        user = update.effective_user
        name = update.message.text.strip()

        try:
            request = RegisterEmployeeRequest(
                telegram_id=str(user.id),
                name=name
            )
            employee = self.register_employee_use_case.execute(request)

            await update.message.reply_text(f"ការចុះឈ្មោះជោគជ័យ! ស្វាគមន៍ {employee.name}!")
            await show_menu_callback(update, context, employee.name)
        except ValueError as e:
            await update.message.reply_text(f"កំហុស: {str(e)}")

        return ConversationHandler.END
