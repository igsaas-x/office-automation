from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from ...application.use_cases.record_check_in import RecordCheckInUseCase
from ...application.use_cases.get_employee import GetEmployeeUseCase
from ...application.dto.check_in_dto import CheckInRequest

WAITING_LOCATION = 1

class CheckInHandler:
    def __init__(
        self,
        record_check_in_use_case: RecordCheckInUseCase,
        get_employee_use_case: GetEmployeeUseCase
    ):
        self.record_check_in_use_case = record_check_in_use_case
        self.get_employee_use_case = get_employee_use_case

    async def request_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Request location for check-in"""
        keyboard = [[KeyboardButton("📍 Share Location", request_location=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

        await update.message.reply_text(
            "Please share your location to check in:",
            reply_markup=reply_markup
        )
        return WAITING_LOCATION

    async def process_check_in(self, update: Update, context: ContextTypes.DEFAULT_TYPE, show_menu_callback):
        """Process location and save check-in"""
        user = update.effective_user
        location = update.message.location

        # Get employee
        employee = self.get_employee_use_case.execute_by_telegram_id(str(user.id))

        if not employee:
            await update.message.reply_text("Please register first using /start")
            return ConversationHandler.END

        try:
            request = CheckInRequest(
                employee_id=employee.id,
                latitude=location.latitude,
                longitude=location.longitude
            )
            response = self.record_check_in_use_case.execute(request)

            await update.message.reply_text(
                f"✅ {response.message}\n"
                f"Time: {response.timestamp}\n"
                f"Location: {response.location}"
            )
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

        await show_menu_callback(update, context, employee.name)
        return ConversationHandler.END
