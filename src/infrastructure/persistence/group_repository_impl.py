from typing import Optional, List
from sqlalchemy.orm import Session
from ...domain.entities.group import Group
from ...domain.repositories.group_repository import IGroupRepository
from .models import GroupModel

class GroupRepository(IGroupRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, group: Group) -> Group:
        if group.id:
            # Update existing
            db_group = self.session.query(GroupModel).filter_by(id=group.id).first()
            db_group.name = group.name
            db_group.chat_id = group.chat_id
            db_group.business_name = group.business_name
            db_group.package_level = group.package_level
            db_group.package_updated_at = group.package_updated_at
            db_group.package_updated_by = group.package_updated_by
            db_group.created_by_telegram_id = group.created_by_telegram_id
            db_group.created_by_username = group.created_by_username
            db_group.created_by_first_name = group.created_by_first_name
            db_group.created_by_last_name = group.created_by_last_name
        else:
            # Create new
            db_group = GroupModel(
                chat_id=group.chat_id,
                name=group.name,
                business_name=group.business_name,
                package_level=group.package_level,
                package_updated_at=group.package_updated_at,
                package_updated_by=group.package_updated_by,
                created_by_telegram_id=group.created_by_telegram_id,
                created_by_username=group.created_by_username,
                created_by_first_name=group.created_by_first_name,
                created_by_last_name=group.created_by_last_name,
                created_at=group.created_at
            )
            self.session.add(db_group)

        self.session.commit()
        self.session.refresh(db_group)

        return self._to_entity(db_group)

    def find_by_id(self, group_id: int) -> Optional[Group]:
        db_group = self.session.query(GroupModel).filter_by(id=group_id).first()
        return self._to_entity(db_group) if db_group else None

    def find_by_chat_id(self, chat_id: str) -> Optional[Group]:
        db_group = self.session.query(GroupModel).filter_by(chat_id=chat_id).first()
        return self._to_entity(db_group) if db_group else None

    def find_all(self) -> List[Group]:
        db_groups = self.session.query(GroupModel).all()
        return [self._to_entity(db_group) for db_group in db_groups]

    def _to_entity(self, model: GroupModel) -> Group:
        return Group(
            id=model.id,
            chat_id=model.chat_id,
            name=model.name,
            business_name=model.business_name,
            package_level=model.package_level,
            package_updated_at=model.package_updated_at,
            package_updated_by=model.package_updated_by,
            created_by_telegram_id=model.created_by_telegram_id,
            created_by_username=model.created_by_username,
            created_by_first_name=model.created_by_first_name,
            created_by_last_name=model.created_by_last_name,
            created_at=model.created_at
        )
