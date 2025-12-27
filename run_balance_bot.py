from src.infrastructure.telegram.balance_bot_app import BalanceBotApplication
from src.infrastructure.utils.logging_config import setup_logging


def main():
    """Run balance bot only"""
    setup_logging()
    bot = BalanceBotApplication()
    bot.run()


if __name__ == '__main__':
    main()
