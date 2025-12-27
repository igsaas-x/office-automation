#!/usr/bin/env python3
"""
Flask API server for Office Automation Mini App
"""
import os
from src.infrastructure.api.flask_app import create_app
from src.infrastructure.persistence.database import database
from src.infrastructure.utils.logging_config import setup_logging

def main():
    setup_logging()
    # Initialize database
    database.create_tables()

    # Create Flask app
    app = create_app()

    # Get configuration from environment
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', '5000'))
    debug = os.getenv('API_DEBUG', 'False').lower() == 'true'

    print(f"Starting Flask API server on {host}:{port}")
    print(f"Debug mode: {debug}")

    # Run the app
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()
