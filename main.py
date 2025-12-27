import multiprocessing
import sys
import os
from src.infrastructure.telegram.bot_app import BotApplication
from src.infrastructure.telegram.balance_bot_app import BalanceBotApplication
from src.infrastructure.api.flask_app import create_app
from src.infrastructure.persistence.database import database
from src.infrastructure.config.settings import settings
from src.infrastructure.utils.logging_config import setup_logging


def run_checkin_bot():
    """Run the check-in bot in a separate process"""
    setup_logging()
    settings.load_admin_ids([
        # 123456789,  # Replace with actual admin telegram IDs
    ])
    bot = BotApplication()
    bot.run()


def run_balance_bot():
    """Run the balance bot in a separate process"""
    setup_logging()
    bot = BalanceBotApplication()
    bot.run()


def run_api_server():
    """Run the Flask API server in a separate process"""
    setup_logging()
    # Initialize database
    database.create_tables()

    # Create Flask app
    app = create_app()

    # Get configuration from environment
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', '80'))
    debug = os.getenv('API_DEBUG', 'False').lower() == 'true'

    print(f"Starting Flask API server on {host}:{port}")
    print(f"Debug mode: {debug}")

    # Run the app
    app.run(host=host, port=port, debug=debug, use_reloader=False)


def main():
    """Main entry point - runs both bots and API server in separate processes"""
    # Use 'fork' on Unix systems for proper initialization
    if sys.platform != 'win32':
        multiprocessing.set_start_method('fork', force=True)

    # Create processes for each component
    checkin_process = multiprocessing.Process(target=run_checkin_bot, name="CheckinBot")
    balance_process = multiprocessing.Process(target=run_balance_bot, name="BalanceBot")
    api_process = multiprocessing.Process(target=run_api_server, name="APIServer")

    try:
        # Start all processes
        print("Starting Office Automation System...")
        print("- Check-in Bot")
        print("- Balance Bot")
        print("- Flask API Server")

        checkin_process.start()
        balance_process.start()
        api_process.start()

        # Wait for all processes
        checkin_process.join()
        balance_process.join()
        api_process.join()

    except KeyboardInterrupt:
        print("\nStopping all services...")
        checkin_process.terminate()
        balance_process.terminate()
        api_process.terminate()
        checkin_process.join()
        balance_process.join()
        api_process.join()
        print("All services stopped by user")


if __name__ == '__main__':
    main()
