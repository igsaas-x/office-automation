"""
MongoDB connection manager for OpnForm integration

This module provides a singleton connection to MongoDB for storing
form submissions, customer configurations, and related data.
"""

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from typing import Optional

from ..config.settings import settings

logger = logging.getLogger(__name__)


class MongoDBConnection:
    """
    Singleton class for managing MongoDB connection

    Provides a single instance of MongoDB client and database
    with automatic index creation and connection management.
    """

    _instance: Optional['MongoDBConnection'] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self) -> Database:
        """
        Get MongoDB database connection

        Creates connection if not exists, otherwise returns existing connection.
        Also creates necessary indexes on first connection.

        Returns:
            Database: MongoDB database instance

        Raises:
            ConnectionFailure: If unable to connect to MongoDB
        """
        if self._client is None:
            try:
                logger.info(f"Connecting to MongoDB at {settings.MONGODB_URL}")

                self._client = MongoClient(
                    settings.MONGODB_URL,
                    maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
                    serverSelectionTimeoutMS=5000,  # 5 second timeout
                    connectTimeoutMS=5000
                )

                # Test connection
                self._client.admin.command('ping')
                logger.info("MongoDB connection successful")

                self._db = self._client[settings.MONGODB_DATABASE]
                self._create_indexes()

            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise ConnectionFailure(
                    f"Could not connect to MongoDB at {settings.MONGODB_URL}. "
                    "Please ensure MongoDB is running and accessible."
                )

        return self._db

    def _create_indexes(self):
        """
        Create necessary indexes for collections

        This method is called once when connection is first established.
        Indexes improve query performance and enforce uniqueness constraints.
        """
        try:
            logger.info("Creating MongoDB indexes...")

            # Admin users collection indexes
            self._db.admin_users.create_index("telegram_id", unique=True)
            self._db.admin_users.create_index("username")

            # Customers collection indexes (for OpnForm)
            self._db.customers.create_index("telegram_user_id", unique=True)
            self._db.customers.create_index("telegram_group_id")
            self._db.customers.create_index("webhook_endpoint", unique=True)
            self._db.customers.create_index("status")

            # Form configurations indexes
            self._db.form_configurations.create_index(
                [("customer_id", 1), ("opnform_form_id", 1)],
                unique=True
            )
            self._db.form_configurations.create_index([("customer_id", 1), ("is_active", 1)])

            # Form submissions indexes
            self._db.form_submissions.create_index([("customer_id", 1), ("created_at", -1)])
            self._db.form_submissions.create_index([("form_config_id", 1), ("created_at", -1)])
            self._db.form_submissions.create_index("opnform_submission_id", unique=True)
            self._db.form_submissions.create_index([("metadata.submitted_at", -1)])
            self._db.form_submissions.create_index("processing_status")

            # Report cache indexes
            self._db.report_cache.create_index([
                ("customer_id", 1),
                ("form_config_id", 1),
                ("report_type", 1),
                ("report_date", -1)
            ])
            self._db.report_cache.create_index("expires_at", expireAfterSeconds=0)  # TTL index

            # Add telegram_group_chat_id index to form_configurations (for linking to MySQL groups)
            self._db.form_configurations.create_index("telegram_group_chat_id")

            logger.info("MongoDB indexes created successfully")

        except Exception as e:
            logger.warning(f"Error creating indexes (they may already exist): {e}")

    def close(self):
        """Close MongoDB connection"""
        if self._client:
            logger.info("Closing MongoDB connection")
            self._client.close()
            self._client = None
            self._db = None

    def get_database(self) -> Database:
        """
        Get MongoDB database instance

        Alias for connect() method for better readability.

        Returns:
            Database: MongoDB database instance
        """
        return self.connect()


# Singleton instance
mongodb = MongoDBConnection()
