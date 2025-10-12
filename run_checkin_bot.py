from src.infrastructure.telegram.bot_app import BotApplication
from src.infrastructure.config.settings import settings


def main():
    """Run check-in bot only"""
    # Configure admin IDs (replace with actual telegram user IDs)
    settings.load_admin_ids([
        # 123456789,  # Replace with actual admin telegram IDs
    ])

    # Start check-in bot
    bot = BotApplication()
    bot.run()


if __name__ == '__main__':
    main()
