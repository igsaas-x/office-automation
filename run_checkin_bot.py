from src.infrastructure.telegram.bot_app import BotApplication
from src.infrastructure.config.settings import settings
from src.infrastructure.utils.logging_config import setup_logging


def main():
    """Run check-in bot only"""
    setup_logging()
    # Configure admin IDs (replace with actual telegram user IDs)
    settings.load_admin_ids([
        # 123456789,  # Replace with actual admin telegram IDs
    ])

    # Start check-in bot
    bot = BotApplication()
    bot.run()


if __name__ == '__main__':
    main()
