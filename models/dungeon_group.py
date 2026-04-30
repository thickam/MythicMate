from abc import ABC, abstractmethod
from typing import Optional

from discord import Embed, InteractionMessage, Member, User
from discord.interactions import InteractionChannel

from models.role import Role

class DungeonGroup(ABC):
    @abstractmethod
    def is_complete(self) -> bool:
        pass

    @abstractmethod
    def update_group_embed(self, message: InteractionMessage, embed: Embed):
        pass

    @abstractmethod
    def add_member(self, role: Role, user: Optional[User | Member] = None, user_id: Optional[str] = None):
        pass

    @abstractmethod
    def remove_user(self, user: User | Member) -> tuple[Optional[Role], Optional[str]]:
        pass

    @abstractmethod
    def get_user_role(self, user_id: str) -> tuple[Role, bool]:
        pass

    @abstractmethod
    def send_reminder(self, channel: InteractionChannel | None):
        pass

    @property
    @abstractmethod
    def reminder_task(self):
        pass
