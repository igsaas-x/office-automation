import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Bot tokens
    CHECKIN_BOT_TOKEN: str = os.getenv('CHECKIN_BOT_TOKEN')  # For check-in, registration, salary advance
    BALANCE_BOT_TOKEN: str = os.getenv('BALANCE_BOT_TOKEN')  # For balance summary
    BOT_TOKEN: str = os.getenv('BOT_TOKEN')  # Backward compatibility (same as CHECKIN_BOT_TOKEN)

    # Database configuration
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: str = os.getenv('DB_PORT', '3306')
    DB_USER: str = os.getenv('DB_USER', 'root')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')
    DB_NAME: str = os.getenv('DB_NAME', 'office_automation')

    # Google Sheets configuration
    BALANCE_SHEET_ID: str = os.getenv('BALANCE_SHEET_ID', '')
    BALANCE_SHEET_NAME: str = os.getenv('BALANCE_SHEET_NAME', 'October')
    MUSIC_SCHOOL_SHEET_ID: str = os.getenv('MUSIC_SCHOOL_SHEET_ID', '1vSjYtvKxQPdFUrowO2kd7bXoU9bwd_Tpf06Twdw_4YU')

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Telegram authentication configuration
    TELEGRAM_AUTH_ENABLED: bool = os.getenv('TELEGRAM_AUTH_ENABLED', 'true').lower() == 'true'
    TELEGRAM_AUTH_STRICT_MODE: bool = os.getenv('TELEGRAM_AUTH_STRICT_MODE', 'true').lower() == 'true'
    TELEGRAM_INITDATA_MAX_AGE: int = int(os.getenv('TELEGRAM_INITDATA_MAX_AGE', '3600'))  # 1 hour
    TELEGRAM_AUTH_CACHE_TTL: int = int(os.getenv('TELEGRAM_AUTH_CACHE_TTL', '300'))  # 5 minutes
    TELEGRAM_RATE_LIMIT_PER_USER: int = int(os.getenv('TELEGRAM_RATE_LIMIT_PER_USER', '20'))
    TELEGRAM_RATE_LIMIT_WINDOW: int = int(os.getenv('TELEGRAM_RATE_LIMIT_WINDOW', '60'))  # seconds
    TELEGRAM_AUTH_EXEMPT_PATHS: str = os.getenv('TELEGRAM_AUTH_EXEMPT_PATHS', '/health,/api-docs,/metrics')

    ADMIN_IDS: list[int] = []

    @classmethod
    def load_admin_ids(cls, admin_ids: list[int]):
        cls.ADMIN_IDS = admin_ids

settings = Settings()
