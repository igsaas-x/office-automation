"""
Group Registration Handler
Handles /register command to register Telegram groups as businesses
"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from ...application.use_cases.register_group import RegisterGroupUseCase
from ...domain.repositories.group_repository import IGroupRepository
from ...domain.repositories.telegram_user_repository import ITelegramUserRepository

# Conversation states
WAITING_FOR_BUSINESS_NAME = 1


class RegistrationHandler:
    """Handler for group registration"""

    def __init__(
        self,
        register_group_use_case: RegisterGroupUseCase,
        group_repository: IGroupRepository,
        telegram_user_repository: ITelegramUserRepository
    ):
        self.register_group_use_case = register_group_use_case
        self.group_repository = group_repository
        self.telegram_user_repository = telegram_user_repository

    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /register command in group
        Initiates the group registration process
        """
        chat = update.effective_chat

        # Only works in group chats
        if chat.type not in ['group', 'supergroup']:
            await update.message.reply_text(
                "⛔ ពាក្យបញ្ជានេះដំណើរការតែនៅក្នុងការសន្ទនាក្រុមប៉ុណ្ណោះ។\n\n"
                "Please add me to your business group and run this command there."
            )
            return ConversationHandler.END

        # Check if already registered
        existing_group = self.group_repository.find_by_chat_id(str(chat.id))

        if existing_group:
            # Group already registered, show info and menu link
            bot_username = context.bot.username

            await update.message.reply_text(
                f"✅ ក្រុមនេះត្រូវបានចុះឈ្មោះរួចហើយ!\n\n"
                f"**ឈ្មោះអាជីវកម្ម:** {existing_group.business_name or existing_group.name}\n"
                f"**កញ្ចប់:** {existing_group.package_level.title()}\n\n"
                f"💡 **របៀបប្រើប្រាស់:**\n"
                f"នៅក្នុងក្រុមនេះ រត់ពាក្យបញ្ជា /menu ដើម្បីចូលប្រើប្រព័ន្ធ។\n\n"
                f"This group is already registered!\n"
                f"**Business Name:** {existing_group.business_name or existing_group.name}\n"
                f"**Package:** {existing_group.package_level.title()}\n\n"
                f"💡 **How to use:**\n"
                f"Run /menu command in this group to access the system.",
                parse_mode='Markdown'
            )
            return ConversationHandler.END

        # Prompt for business name
        await update.message.reply_text(
            "📝 **ការចុះឈ្មោះអាជីវកម្ម**\n\n"
            "សូមបញ្ចូលឈ្មោះអាជីវកម្ម ឬសាខារបស់អ្នក:\n\n"
            "**Business Registration**\n"
            "Please enter your business or branch name:",
            parse_mode='Markdown'
        )

        return WAITING_FOR_BUSINESS_NAME

    async def receive_business_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Receive and save business name, then confirm registration
        """
        business_name = update.message.text.strip()
        chat = update.effective_chat
        user = update.effective_user

        # Validate business name
        if len(business_name) < 3:
            await update.message.reply_text(
                "⚠️ ឈ្មោះអាជីវកម្មត្រូវតែមានយ៉ាងហោចណាស់ ៣ តួអក្សរ។\n"
                "សូមព្យាយាមម្តងទៀត:\n\n"
                "Business name must be at least 3 characters.\n"
                "Please try again:"
            )
            return WAITING_FOR_BUSINESS_NAME

        # Register the group
        group = self.register_group_use_case.execute(
            chat_id=str(chat.id),
            name=chat.title or "ក្រុមមិនស្គាល់",
            business_name=business_name,
            created_by_telegram_id=str(user.id) if user else None,
            created_by_username=user.username if user else None,
            created_by_first_name=user.first_name if user else None,
            created_by_last_name=user.last_name if user else None
        )

        # Send confirmation
        await update.message.reply_text(
            f"✅ **ការចុះឈ្មោះជោគជ័យ!**\n\n"
            f"**ឈ្មោះអាជីវកម្ម:** {business_name}\n"
            f"**Group ID:** `{chat.id}`\n"
            f"**កញ្ចប់:** Free (ទាក់ទង @AutosumSupport ដើម្បីដំឡើង)\n\n"
            f"📋 **ជំហានបន្ទាប់:**\n"
            f"1. បន្ថែមបុគ្គលិកទាំងអស់ទៅក្នុងក្រុម Telegram នេះ\n"
            f"2. បុគ្គលិកអាចប្រើពាក្យបញ្ជា /menu ដើម្បីចូលប្រើប្រព័ន្ធ\n"
            f"3. ការចុះឈ្មោះទាំងអស់នឹងត្រូវបានភ្ជាប់ជាមួយ {business_name} ដោយស្វ័យប្រវត្តិ\n\n"
            f"💡 **គន្លឹះ:** សាកល្បងពាក្យបញ្ជា /menu ឥឡូវនេះ ដើម្បីមើលមុខងារដែលមាន!\n\n"
            f"---\n\n"
            f"✅ **Registration Successful!**\n\n"
            f"**Business Name:** {business_name}\n"
            f"**Group ID:** `{chat.id}`\n"
            f"**Package:** Free (contact @AutosumSupport to upgrade)\n\n"
            f"📋 **Next Steps:**\n"
            f"1. Add all employees to this Telegram group\n"
            f"2. Employees can use /menu command to access check-in and other features\n"
            f"3. All check-ins will automatically be associated with {business_name}\n\n"
            f"💡 **Tip:** Try the /menu command now to see available actions!",
            parse_mode='Markdown'
        )

        return ConversationHandler.END
