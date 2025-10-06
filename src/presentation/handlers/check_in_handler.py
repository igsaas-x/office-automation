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
        chat = update.effective_chat

        # If the user taps the button inside a group, store the group and redirect to private chat
        if chat.type in ['group', 'supergroup']:
            context.user_data['check_in_group'] = {
                'chat_id': chat.id,
                'title': chat.title
            }

            bot_username = context.bot.username
            deep_link = f"https://t.me/{bot_username}?start=checkin" if bot_username else "https://t.me"

            await update.message.reply_text(
                "I can only request your location in a private chat."
                "\nTap this link to continue: "
                f"{deep_link}"
                "\nOnce there, press '📍 Check In' again to finish your check-in.",
                disable_web_page_preview=True
            )
            return ConversationHandler.END

        # In private chat we must already know which group to record the check-in for
        group_context = context.user_data.get('check_in_group')
        if not group_context:
            await update.message.reply_text(
                "I don't know which group to check you into."
                "\nGo back to the group chat and press '📍 Check In' there first."
            )
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

        # Identify the correct group to record the check-in against
        if chat.type in ['group', 'supergroup']:
            target_chat_id = chat.id
            target_chat_title = chat.title
        else:
            group_context = context.user_data.get('check_in_group')
            if not group_context:
                await update.message.reply_text(
                    "I don't know which group to check you into."
                    "\nGo back to the group chat and press '📍 Check In' there first."
                )
                return ConversationHandler.END

            target_chat_id = group_context['chat_id']
            target_chat_title = group_context.get('title')

        # Get employee
        employee = self.get_employee_use_case.execute_by_telegram_id(str(user.id))

        if not employee:
            await update.message.reply_text("Please register first using /start in a private chat with the bot.")
            return ConversationHandler.END

        try:
            # Register or get group
            group = self.register_group_use_case.execute(
                chat_id=str(target_chat_id),
                name=target_chat_title or f"Group {target_chat_id}"
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
            # Clear stored group context once the check-in succeeds
            context.user_data.pop('check_in_group', None)

            await show_menu_callback(update, context, employee.name)
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

        return ConversationHandler.END
