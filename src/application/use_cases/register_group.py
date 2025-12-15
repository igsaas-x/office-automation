from ...domain.entities.group import Group
from ...domain.repositories.group_repository import IGroupRepository
from typing import Optional

class RegisterGroupUseCase:
    def __init__(self, group_repository: IGroupRepository):
        self.group_repository = group_repository

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
        if existing_group:
            # Update owner info if not set
            if not existing_group.created_by_telegram_id and created_by_telegram_id:
                existing_group.created_by_telegram_id = created_by_telegram_id
                existing_group.created_by_username = created_by_username
                existing_group.created_by_first_name = created_by_first_name
                existing_group.created_by_last_name = created_by_last_name
                return self.group_repository.save(existing_group)
            return existing_group

        # Create new group
        group = Group.create(
            chat_id=chat_id,
            name=name,
            created_by_telegram_id=created_by_telegram_id,
            created_by_username=created_by_username,
            created_by_first_name=created_by_first_name,
            created_by_last_name=created_by_last_name
        )

        # Save to repository
        return self.group_repository.save(group)
