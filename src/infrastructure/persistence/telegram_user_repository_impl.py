from typing import Optional
from sqlalchemy.orm import Session
from ...domain.entities.telegram_user import TelegramUser
from ...domain.repositories.telegram_user_repository import ITelegramUserRepository
from .models import TelegramUserModel
from datetime import datetime, timezone

class TelegramUserRepository(ITelegramUserRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, user: TelegramUser) -> TelegramUser:
        if user.id:
            # Update existing
            db_user = self.session.query(TelegramUserModel).filter_by(id=user.id).first()
            db_user.username = user.username
            db_user.first_name = user.first_name
            db_user.last_name = user.last_name
            db_user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        else:
            # Check if user exists by telegram_id
            db_user = self.session.query(TelegramUserModel).filter_by(telegram_id=user.telegram_id).first()

            if db_user:
                # Update existing user
                db_user.username = user.username
                db_user.first_name = user.first_name
                db_user.last_name = user.last_name
                db_user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            else:
                # Create new
                db_user = TelegramUserModel(
                    telegram_id=user.telegram_id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    created_at=user.created_at,
                    updated_at=user.updated_at
                )
                self.session.add(db_user)

        self.session.commit()
        self.session.refresh(db_user)

        return self._to_entity(db_user)

    def find_by_telegram_id(self, telegram_id: str) -> Optional[TelegramUser]:
        db_user = self.session.query(TelegramUserModel).filter_by(telegram_id=telegram_id).first()
        return self._to_entity(db_user) if db_user else None

    def find_by_id(self, user_id: int) -> Optional[TelegramUser]:
        db_user = self.session.query(TelegramUserModel).filter_by(id=user_id).first()
        return self._to_entity(db_user) if db_user else None

    def _to_entity(self, model: TelegramUserModel) -> TelegramUser:
        return TelegramUser(
            id=model.id,
            telegram_id=model.telegram_id,
            username=model.username,
            first_name=model.first_name,
            last_name=model.last_name,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
