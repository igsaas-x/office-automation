import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Bot tokens
    CHECKIN_BOT_TOKEN: str = os.getenv('CHECKIN_BOT_TOKEN')  # For check-in, registration, salary advance
    BALANCE_BOT_TOKEN: str = os.getenv('BALANCE_BOT_TOKEN')  # For balance summary
    BOT_TOKEN: str = os.getenv('BOT_TOKEN')  # Backward compatibility (same as CHECKIN_BOT_TOKEN)

    # MySQL Database configuration
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: str = os.getenv('DB_PORT', '3306')
    DB_USER: str = os.getenv('DB_USER', 'root')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')
    DB_NAME: str = os.getenv('DB_NAME', 'office_automation')

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # MongoDB configuration (for OpnForm integration)
    MONGODB_URL: str = os.getenv('MONGODB_URL', 'MONGODB_URL=mongodb://rootUser:rootPassword@localhost:27017/')
    MONGODB_DATABASE: str = os.getenv('MONGODB_DATABASE', 'office_automation_forms')
    MONGODB_MAX_POOL_SIZE: int = int(os.getenv('MONGODB_MAX_POOL_SIZE', '10'))

    # JWT configuration (for admin portal authentication)
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', 'azd34##dsf09900011FF$$')
    JWT_ACCESS_TOKEN_EXPIRES: int = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '28800'))  # 8 hours in seconds
    JWT_REFRESH_TOKEN_EXPIRES: int = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', '2592000'))  # 30 days in seconds
    JWT_ALGORITHM: str = os.getenv('JWT_ALGORITHM', 'HS256')

    # Admin portal configuration
    ADMIN_TELEGRAM_IDS: str = os.getenv('ADMIN_TELEGRAM_IDS', '570671598')  # Comma-separated list of admin Telegram IDs
    ADMIN_PORTAL_URL: str = os.getenv('ADMIN_PORTAL_URL', 'http://localhost:3000')
    CORS_ALLOWED_ORIGINS: str = os.getenv('CORS_ALLOWED_ORIGINS', '*')

    # OpnForm integration
    OPNFORM_API_URL: str = os.getenv('OPNFORM_API_URL', 'https://api.opnform.com/api/v1')
    OPNFORM_WORKSPACE_ID: str = os.getenv('OPNFORM_WORKSPACE_ID', '12030')
    OPNFORM_API_TOKEN: str = os.getenv('OPNFORM_API_TOKEN', 'w6mFkuHiNUQwD3O7YMDAYiESX3BhmPjln974vioUdfa1a34d')

    # Google Sheets configuration
    BALANCE_SHEET_ID: str = os.getenv('BALANCE_SHEET_ID', '')
    BALANCE_SHEET_NAME: str = os.getenv('BALANCE_SHEET_NAME', 'October')
    MUSIC_SCHOOL_SHEET_ID: str = os.getenv('MUSIC_SCHOOL_SHEET_ID', '1vSjYtvKxQPdFUrowO2kd7bXoU9bwd_Tpf06Twdw_4YU')

    # Telegram authentication configuration (for miniapp/user app)
    TELEGRAM_AUTH_ENABLED: bool = os.getenv('TELEGRAM_AUTH_ENABLED', 'true').lower() == 'true'
    TELEGRAM_AUTH_STRICT_MODE: bool = os.getenv('TELEGRAM_AUTH_STRICT_MODE', 'true').lower() == 'true'
    TELEGRAM_INITDATA_MAX_AGE: int = int(os.getenv('TELEGRAM_INITDATA_MAX_AGE', '3600'))  # 1 hour
    TELEGRAM_AUTH_CACHE_TTL: int = int(os.getenv('TELEGRAM_AUTH_CACHE_TTL', '300'))  # 5 minutes
    TELEGRAM_RATE_LIMIT_PER_USER: int = int(os.getenv('TELEGRAM_RATE_LIMIT_PER_USER', '20'))
    TELEGRAM_RATE_LIMIT_WINDOW: int = int(os.getenv('TELEGRAM_RATE_LIMIT_WINDOW', '60'))  # seconds
    TELEGRAM_AUTH_EXEMPT_PATHS: str = os.getenv('TELEGRAM_AUTH_EXEMPT_PATHS', '/health,/api-docs,/metrics,/api/auth,/api/admin,/api/webhooks')

    ADMIN_IDS: list[int] = []

    @classmethod
    def load_admin_ids(cls, admin_ids: list[int]):
        cls.ADMIN_IDS = admin_ids

    def get_admin_telegram_ids(self) -> list[str]:
        """Get list of admin Telegram IDs as strings"""
        if not self.ADMIN_TELEGRAM_IDS:
            return []
        return [id.strip() for id in self.ADMIN_TELEGRAM_IDS.split(',') if id.strip()]

    def get_cors_origins(self) -> list[str]:
        """Get list of allowed CORS origins"""
        if not self.CORS_ALLOWED_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(',') if origin.strip()]

settings = Settings()
