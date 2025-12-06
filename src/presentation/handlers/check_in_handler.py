from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import TelegramError
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
        message = update.effective_message

        # If the user taps the button inside a group, store the group and redirect to private chat
        if chat.type in ['group', 'supergroup']:
            context.user_data['check_in_group'] = {
                'chat_id': chat.id,
                'title': chat.title,
                'username': chat.username
            }
            context.user_data['pending_checkin_command'] = True

            bot_username = context.bot.username
            deep_link = f"https://t.me/{bot_username}?start=checkin" if bot_username else "https://t.me"

            keyboard = [[InlineKeyboardButton("ទៅកាន់ការចុះឈ្មោះ", url=deep_link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if update.callback_query:
                await update.callback_query.edit_message_text(
                    "ចុចប៊ូតុងខាងក្រោមដើម្បីបើកការសន្ទនាឯកជន និងបញ្ចប់ការចុះឈ្មោះរបស់អ្នក។",
                    reply_markup=reply_markup
                )
                # Store message ID to remove button later
                context.user_data['check_in_message_id'] = update.callback_query.message.message_id
            else:
                sent_msg = await message.reply_text(
                    "ចុចប៊ូតុងខាងក្រោមដើម្បីបើកការសន្ទនាឯកជន និងបញ្ចប់ការចុះឈ្មោះរបស់អ្នក។",
                    reply_markup=reply_markup
                )
                # Store message ID to remove button later
                context.user_data['check_in_message_id'] = sent_msg.message_id
            return ConversationHandler.END

        # In private chat we must already know which group to record the check-in for
        group_context = context.user_data.get('check_in_group')
        if not group_context:
            await message.reply_text(
                "ខ្ញុំមិនដឹងថាត្រូវចុះឈ្មោះអ្នកទៅក្រុមណាទេ។"
                "\nសូមត្រឡប់ទៅការសន្ទនាក្រុម ហើយចុចប៊ូតុង '📍 ចុះឈ្មោះ' នៅទីនោះសិន។"
            )
            return ConversationHandler.END

        keyboard = [[KeyboardButton("📍 ចែករំលែកទីតាំង", request_location=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

        await message.reply_text(
            "សូមចែករំលែកទីតាំងរបស់អ្នកដើម្បីចុះឈ្មោះ:",
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
            target_chat_username = getattr(chat, 'username', None)
        else:
            group_context = context.user_data.get('check_in_group')
            if not group_context:
                await update.message.reply_text(
                    "ខ្ញុំមិនដឹងថាត្រូវចុះឈ្មោះអ្នកទៅក្រុមណាទេ។"
                    "\nសូមត្រឡប់ទៅការសន្ទនាក្រុម ហើយចុចប៊ូតុង '📍 ចុះឈ្មោះ' នៅទីនោះសិន។"
                )
                return ConversationHandler.END

            target_chat_id = group_context['chat_id']
            target_chat_title = group_context.get('title')
            target_chat_username = group_context.get('username')

        # Get employee
        employee = self.get_employee_use_case.execute_by_telegram_id(str(user.id))

        if not employee:
            await update.message.reply_text("សូមចុះឈ្មោះជាមុនសិនដោយប្រើ /register")
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

            group_name = target_chat_title or f"ក្រុម {target_chat_id}"
            await update.message.reply_text(
                f"✅ {response.message}\n"
                f"បុគ្គលិក: {employee.name}\n"
                f"ក្រុម: {group_name}\n"
                f"ពេលវេលា: {response.timestamp}\n"
                f"ទីតាំង: {response.location}"
            )
            # Share a link back to the originating group in the private chat
            if chat.type not in ['group', 'supergroup']:
                group_name = target_chat_title or "ក្រុមរបស់អ្នក"
                if target_chat_username:
                    group_link = f"https://t.me/{target_chat_username}"
                    await update.message.reply_text(
                        f"🔁 ត្រឡប់ទៅ {group_name}: {group_link}",
                        disable_web_page_preview=True
                    )
                else:
                    await update.message.reply_text(
                        f"✅ ការចុះឈ្មោះត្រូវបានកត់ត្រាសម្រាប់ {group_name}"
                    )

            # Notify the group about the successful check-in
            group_message = (
                f"✅ {employee.name} បានចុះឈ្មោះដោយជោគជ័យ។\n"
                f"ពេលវេលា: {response.timestamp}\n"
                f"ទីតាំង: {response.location}"
            )
            try:
                await context.bot.send_message(chat_id=target_chat_id, text=group_message)

                # Remove the "Go to Checkin" button from the group message
                check_in_message_id = context.user_data.get('check_in_message_id')
                if check_in_message_id:
                    try:
                        await context.bot.edit_message_reply_markup(
                            chat_id=target_chat_id,
                            message_id=check_in_message_id,
                            reply_markup=None
                        )
                    except TelegramError:
                        # Ignore if message can't be edited (e.g., too old or deleted)
                        pass
            except TelegramError as notify_error:
                if chat.type not in ['group', 'supergroup']:
                    await update.message.reply_text(
                        "ការចុះឈ្មោះត្រូវបានកត់ត្រា ប៉ុន្តែខ្ញុំមិនអាចជូនដំណឹងដល់ក្រុមបានទេ: "
                        f"{notify_error.message if hasattr(notify_error, 'message') else str(notify_error)}"
                    )
            finally:
                context.user_data.pop('check_in_group', None)
                context.user_data.pop('check_in_message_id', None)

            if chat.type not in ['group', 'supergroup']:
                await show_menu_callback(update, context, employee.name)
        except Exception as e:
            await update.message.reply_text(f"កំហុស: {str(e)}")

        return ConversationHandler.END
