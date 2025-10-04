from ...domain.entities.group import Group
from ...domain.repositories.group_repository import IGroupRepository

class RegisterGroupUseCase:
    def __init__(self, group_repository: IGroupRepository):
        self.group_repository = group_repository

    def execute(self, chat_id: str, name: str) -> Group:
        # Check if group already exists
        existing_group = self.group_repository.find_by_chat_id(chat_id)
        if existing_group:
            return existing_group

        # Create new group
        group = Group.create(
            chat_id=chat_id,
            name=name
        )

        # Save to repository
        return self.group_repository.save(group)
