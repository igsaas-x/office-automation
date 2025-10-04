from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from ...application.use_cases.record_check_in import RecordCheckInUseCase
from ...application.use_cases.get_employee import GetEmployeeUseCase
from ...application.use_cases.register_group import RegisterGroupUseCase
from ...application.use_cases.add_employee_to_group import AddEmployeeToGroupUseCase
from ...application.dto.check_in_dto import CheckInRequest

WAITING_LOCATION = 1

class CheckInHandler:
    def __init__(
        self,
        record_check_in_use_case: RecordCheckInUseCase,
        get_employee_use_case: GetEmployeeUseCase,
        register_group_use_case: RegisterGroupUseCase,
        add_employee_to_group_use_case: AddEmployeeToGroupUseCase
    ):
        self.record_check_in_use_case = record_check_in_use_case
        self.get_employee_use_case = get_employee_use_case
        self.register_group_use_case = register_group_use_case
        self.add_employee_to_group_use_case = add_employee_to_group_use_case

    async def request_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Request location for check-in"""
        # Check if message is from a group
        chat = update.effective_chat
        if chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("Check-in must be done in a group chat.")
            return ConversationHandler.END

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
        chat = update.effective_chat
        location = update.message.location

        # Verify it's a group
        if chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("Check-in must be done in a group chat.")
            return ConversationHandler.END

        # Get employee
        employee = self.get_employee_use_case.execute_by_telegram_id(str(user.id))

        if not employee:
            await update.message.reply_text("Please register first using /start in a private chat with the bot.")
            return ConversationHandler.END

        try:
            # Register or get group
            group = self.register_group_use_case.execute(
                chat_id=str(chat.id),
                name=chat.title or f"Group {chat.id}"
            )

            # Add employee to group if not already added
            try:
                self.add_employee_to_group_use_case.execute(employee.id, group.id)
            except ValueError:
                # Employee already in group, continue
                pass

            # Record check-in
            request = CheckInRequest(
                employee_id=employee.id,
                group_id=group.id,
                latitude=location.latitude,
                longitude=location.longitude
            )
            response = self.record_check_in_use_case.execute(request)

            await update.message.reply_text(
                f"✅ {response.message}\n"
                f"Employee: {employee.name}\n"
                f"Time: {response.timestamp}\n"
                f"Location: {response.location}"
            )
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

        return ConversationHandler.END
