"""
Telegram Notification Service
Sends notifications to Telegram groups/users from the API
"""
import asyncio
import os
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
        latitude: float = None,
        longitude: float = None,
        photo_url: str = None
    ) -> bool:
        """
        Send check-in notification to group

        Args:
            group_chat_id: Telegram group chat ID
            employee_name: Name of employee who checked in
            timestamp: Check-in timestamp
            location: Location coordinates string
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            photo_url: Optional photo URL

        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        try:
            # Create Google Maps link
            maps_link = ""
            if latitude is not None and longitude is not None:
                maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"

            # Format message
            message = (
                f"✅ **Check-In Alert**\n\n"
                f"👤 **Employee:** {employee_name}\n"
                f"🕒 **Time:** {timestamp}\n"
                f"📍 **Location:** {location}"
            )

            if maps_link:
                message += f"\n🗺️ [View on Google Maps]({maps_link})"

            # Send message synchronously using asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # If photo_url is provided, send photo with caption
                if photo_url:
                    # Convert relative path to absolute if needed
                    photo_path = photo_url.lstrip('/')
                    if os.path.exists(photo_path):
                        with open(photo_path, 'rb') as photo_file:
                            loop.run_until_complete(
                                self.bot.send_photo(
                                    chat_id=group_chat_id,
                                    photo=photo_file,
                                    caption=message,
                                    parse_mode='Markdown'
                                )
                            )
                    else:
                        # If file doesn't exist, just send text message
                        print(f"Photo file not found: {photo_path}")
                        loop.run_until_complete(
                            self.bot.send_message(
                                chat_id=group_chat_id,
                                text=message,
                                parse_mode='Markdown'
                            )
                        )
                else:
                    # Otherwise send text message
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
        latitude: float = None,
        longitude: float = None,
        photo_url: str = None
    ) -> bool:
        """
        Send check-in notification to group (async version)

        Args:
            group_chat_id: Telegram group chat ID
            employee_name: Name of employee who checked in
            timestamp: Check-in timestamp
            location: Location coordinates string
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            photo_url: Optional photo URL

        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        try:
            # Create Google Maps link
            maps_link = ""
            if latitude is not None and longitude is not None:
                maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"

            # Format message
            message = (
                f"✅ **Check-In Alert**\n\n"
                f"👤 **Employee:** {employee_name}\n"
                f"🕒 **Time:** {timestamp}\n"
                f"📍 **Location:** {location}"
            )

            if maps_link:
                message += f"\n🗺️ [View on Google Maps]({maps_link})"

            # If photo_url is provided, send photo with caption
            if photo_url:
                # Convert relative path to absolute if needed
                photo_path = photo_url.lstrip('/')
                if os.path.exists(photo_path):
                    with open(photo_path, 'rb') as photo_file:
                        await self.bot.send_photo(
                            chat_id=group_chat_id,
                            photo=photo_file,
                            caption=message,
                            parse_mode='Markdown'
                        )
                else:
                    # If file doesn't exist, just send text message
                    print(f"Photo file not found: {photo_path}")
                    await self.bot.send_message(
                        chat_id=group_chat_id,
                        text=message,
                        parse_mode='Markdown'
                    )
            else:
                # Otherwise send text message
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
