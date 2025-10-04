import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BOT_TOKEN: str = os.getenv('BOT_TOKEN')

    # Database configuration
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: str = os.getenv('DB_PORT', '3306')
    DB_USER: str = os.getenv('DB_USER', 'root')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')
    DB_NAME: str = os.getenv('DB_NAME', 'office_automation')

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    ADMIN_IDS: list[int] = []

    @classmethod
    def load_admin_ids(cls, admin_ids: list[int]):
        cls.ADMIN_IDS = admin_ids

settings = Settings()
