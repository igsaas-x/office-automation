"""
Telegram Notification Service
Sends notifications to Telegram groups/users from the API
"""
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from ...infrastructure.config.settings import settings


class TelegramNotificationService:
    """Service for sending Telegram notifications from the API"""

    def __init__(self):
        """Initialize the notification service with bot token"""
        bot_token = settings.CHECKIN_BOT_TOKEN or settings.BOT_TOKEN
        if not bot_token:
            raise ValueError("Bot token not configured")
        self.bot = Bot(token=bot_token)

    def send_checkin_notification(
        self,
        group_chat_id: str,
        employee_name: str,
        timestamp: str,
        location: str,
        photo_url: str = None
    ) -> bool:
        """
        Send check-in notification to group

        Args:
            group_chat_id: Telegram group chat ID
            employee_name: Name of employee who checked in
            timestamp: Check-in timestamp
            location: Location coordinates
            photo_url: Optional photo URL

        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        try:
            # Format message
            message = (
                f"✅ **Check-In Alert**\n\n"
                f"👤 **Employee:** {employee_name}\n"
                f"🕒 **Time:** {timestamp}\n"
                f"📍 **Location:** {location}"
            )

            # Send message synchronously using asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                loop.run_until_complete(
                    self.bot.send_message(
                        chat_id=group_chat_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                )
                return True
            finally:
                loop.close()

        except TelegramError as e:
            print(f"Failed to send check-in notification: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error sending notification: {e}")
            return False

    async def send_checkin_notification_async(
        self,
        group_chat_id: str,
        employee_name: str,
        timestamp: str,
        location: str,
        photo_url: str = None
    ) -> bool:
        """
        Send check-in notification to group (async version)

        Args:
            group_chat_id: Telegram group chat ID
            employee_name: Name of employee who checked in
            timestamp: Check-in timestamp
            location: Location coordinates
            photo_url: Optional photo URL

        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        try:
            # Format message
            message = (
                f"✅ **Check-In Alert**\n\n"
                f"👤 **Employee:** {employee_name}\n"
                f"🕒 **Time:** {timestamp}\n"
                f"📍 **Location:** {location}"
            )

            await self.bot.send_message(
                chat_id=group_chat_id,
                text=message,
                parse_mode='Markdown'
            )
            return True

        except TelegramError as e:
            print(f"Failed to send check-in notification: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error sending notification: {e}")
            return False


# Singleton instance
_notification_service = None


def get_notification_service() -> TelegramNotificationService:
    """Get or create the notification service singleton"""
    global _notification_service
    if _notification_service is None:
        _notification_service = TelegramNotificationService()
    return _notification_service
