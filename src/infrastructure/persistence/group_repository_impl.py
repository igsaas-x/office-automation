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
        else:
            # Create new
            db_group = GroupModel(
                chat_id=group.chat_id,
                name=group.name,
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
            created_at=model.created_at
        )
