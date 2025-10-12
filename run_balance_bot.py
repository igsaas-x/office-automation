from src.infrastructure.telegram.balance_bot_app import BalanceBotApplication


def main():
    """Run balance bot only"""
    bot = BalanceBotApplication()
    bot.run()


if __name__ == '__main__':
    main()
