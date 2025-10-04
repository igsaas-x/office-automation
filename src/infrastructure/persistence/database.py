from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base
from ..config.settings import settings

class Database:
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()

database = Database()
