from abc import abstractmethod
from collections import namedtuple
from typing import Optional

from discord import Embed, Guild, InteractionMessage, Member, User
from discord.interactions import InteractionChannel

import bot_emoji
from bot_utils import get_mention_str
from models.dungeon_group import DungeonGroup
from models.role import Role

class MultiRoleDungeonGroup(DungeonGroup):
    @property
    def reminder_task(self):
        pass

    def __init__(self):
        self.__members: dict[Role, list[str]] = {
            Role.tank: [],
            Role.healer: [],
            Role.dps: []
        }

    def is_complete(self) -> bool:
        # This is going to be rough -_-
        return False
    
    def __get_user_list(self, guild: Guild | None) -> list[any]:
        user_list: list[tuple[str, list[Role]]] = []
        for role in self.__members.keys():
            

    def update_group_embed(self, message: InteractionMessage, embed: Embed):
        if not message or not embed:
            print("Missing required parameters for update_group_embed")
            return
            
        embed.clear_fields()
        
        tank_emoji = {bot_emoji.get_role_emoji(Role.tank, message.guild)}
        healer_emoji = {bot_emoji.get_role_emoji(Role.healer, message.guild)}
        dps_emoji = {bot_emoji.get_role_emoji(Role.dps, message.guild)}
        # Display main role assignments
        embed.add_field(
            name=f"Interested:",
            value=get_mention_str(self.get_tank()) if self.get_tank() else "None",
            inline=False
        )
        
        # Display DPS slots (filled or empty)
        dps_value = "\n".join([get_mention_str(dps_user) for dps_user in self.get_dps()] + ["None"] * (3 - len(self.get_dps())))
        embed.add_field(
            name=f"{bot_emoji.get_role_emoji(Role.dps, message.guild)} DPS", 
            value=dps_value, 
            inline=False
        )

    def add_member(self, roles: list[Role], user: Optional[User | Member] = None, user_id: Optional[str] = None):
        _user_id = user_id or user.id
        for role in roles:
            if role in self.__members.keys() and _user_id not in self.__members[role]:
                self.__members[role].append(_user_id)

    def remove_user(self, user: User | Member) -> tuple[Optional[Role], Optional[str]]:
        for role in self.__members.keys():
            if user.id in self.__members[role]:
                self.__members[role].remove(user.id)

    def get_user_role(self, user_id: str) -> tuple[Role, bool]:
        user_roles = []
        for role, ids in self.__members.items():
            if user_id in ids:
                user_roles.append(role)
        return user_roles, False
            

    def send_reminder(self, channel: InteractionChannel | None):
        pass