from ...domain.entities.group import Group
from ...domain.entities.telegram_user import TelegramUser
from ...domain.repositories.group_repository import IGroupRepository
from ...domain.repositories.telegram_user_repository import ITelegramUserRepository
from typing import Optional

class RegisterGroupUseCase:
    def __init__(self, group_repository: IGroupRepository, user_repository: ITelegramUserRepository):
        self.group_repository = group_repository
        self.user_repository = user_repository

    def execute(
        self,
        chat_id: str,
        name: str,
        created_by_telegram_id: Optional[str] = None,
        created_by_username: Optional[str] = None,
        created_by_first_name: Optional[str] = None,
        created_by_last_name: Optional[str] = None
    ) -> Group:
        # Check if group already exists
        existing_group = self.group_repository.find_by_chat_id(chat_id)

        # Get or create telegram user
        user_id = None
        if created_by_telegram_id:
            user = self.user_repository.find_by_telegram_id(created_by_telegram_id)
            if not user:
                # Create new user
                user = TelegramUser.create(
                    telegram_id=created_by_telegram_id,
                    username=created_by_username,
                    first_name=created_by_first_name,
                    last_name=created_by_last_name
                )
                user = self.user_repository.save(user)
            else:
                # Update user info if changed
                if (user.username != created_by_username or
                    user.first_name != created_by_first_name or
                    user.last_name != created_by_last_name):
                    user.username = created_by_username
                    user.first_name = created_by_first_name
                    user.last_name = created_by_last_name
                    user = self.user_repository.save(user)

            user_id = user.id

        if existing_group:
            # Update owner if not set
            if not existing_group.created_by_user_id and user_id:
                existing_group.created_by_user_id = user_id
                return self.group_repository.save(existing_group)
            return existing_group

        # Create new group
        group = Group.create(
            chat_id=chat_id,
            name=name,
            created_by_user_id=user_id
        )

        # Save to repository
        return self.group_repository.save(group)
