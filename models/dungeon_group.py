from abc import ABC, abstractmethod
from typing import Optional

from discord import Embed, InteractionMessage, Member, User

from models.role import Role

class DungeonGroup(ABC):
    @abstractmethod
    def is_complete(self) -> bool:
        pass

    @abstractmethod
    def update_group_embed(self, message: InteractionMessage, embed: Embed):
        pass

    @abstractmethod
    def add_member(self, role: list[Role], user: Optional[User | Member] = None, user_id: Optional[str] = None):
        pass

    @abstractmethod
    def remove_user(self, user: User | Member) -> tuple[Optional[Role], Optional[str]]:
        pass

    @abstractmethod
    def remove_user_from_role(self, user: User | Member, role: Role) -> tuple[Optional[Role], Optional[str]]:
        pass

    @abstractmethod
    def get_user_role(self, user_id: str) -> tuple[Role, bool]:
        pass

    @abstractmethod
    def send_reminder(self, channel):
        pass

    @property
    @abstractmethod
    def reminder_task(self):
        pass
