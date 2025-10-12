import multiprocessing
import sys
from src.infrastructure.telegram.bot_app import BotApplication
from src.infrastructure.telegram.balance_bot_app import BalanceBotApplication
from src.infrastructure.config.settings import settings


def run_checkin_bot():
    """Run the check-in bot in a separate process"""
    settings.load_admin_ids([
        # 123456789,  # Replace with actual admin telegram IDs
    ])
    bot = BotApplication()
    bot.run()


def run_balance_bot():
    """Run the balance bot in a separate process"""
    bot = BalanceBotApplication()
    bot.run()


def main():
    """Main entry point - runs both bots in separate processes"""
    # Use 'fork' on Unix systems for proper initialization
    if sys.platform != 'win32':
        multiprocessing.set_start_method('fork', force=True)

    # Create processes for each bot
    checkin_process = multiprocessing.Process(target=run_checkin_bot, name="CheckinBot")
    balance_process = multiprocessing.Process(target=run_balance_bot, name="BalanceBot")

    try:
        # Start both processes
        print("Starting both bots...")
        checkin_process.start()
        balance_process.start()

        # Wait for both processes
        checkin_process.join()
        balance_process.join()

    except KeyboardInterrupt:
        print("\nStopping bots...")
        checkin_process.terminate()
        balance_process.terminate()
        checkin_process.join()
        balance_process.join()
        print("Bots stopped by user")


if __name__ == '__main__':
    main()
