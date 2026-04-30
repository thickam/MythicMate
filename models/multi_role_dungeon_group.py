from abc import abstractmethod
from collections import namedtuple
from datetime import datetime
from typing import Optional

from discord import Embed, Emoji, Guild, Interaction, InteractionMessage, Member, PartialEmoji, User
import discord

import bot_emoji
from bot_utils import get_mention_str
from models.dungeon_group import DungeonGroup
from models.role import Role

class MultiRoleDungeonGroup(DungeonGroup):
    @property
    def reminder_task(self):
        pass

    def __init__(self, interaction: Interaction, initial_role: Role, schedule_time:Optional[datetime]=None):
        self.__members: dict[str, set[Role]] = {}
        self.add_member([initial_role], user=interaction.user)

    def is_complete(self) -> bool:
        # This is going to be rough -_-
        return False

    def __get_member_str(self, role_emoji_dict: dict[Role, Emoji | PartialEmoji | str | None]) -> str :
        individual_member_strings = []
        for user_id, roles in self.__members.items():
            individual_str = f"{get_mention_str(user_id)} -  {" ".join(list(map(lambda role: str(role_emoji_dict[role]), roles)))}"
            individual_member_strings.append(individual_str)
        return "\n".join(individual_member_strings) if individual_member_strings else "Nobody yet..."

    async def update_group_embed(self, message: InteractionMessage, embed: Embed):
        if not message or not embed:
            print("Missing required parameters for update_group_embed")
            return
            
        embed.clear_fields()
        
        tank_emoji = bot_emoji.get_role_emoji(Role.tank, message.guild)
        healer_emoji = bot_emoji.get_role_emoji(Role.healer, message.guild)
        dps_emoji = bot_emoji.get_role_emoji(Role.dps, message.guild)
        role_emoji_dict: dict[Role, Emoji | PartialEmoji | str | None] = {
            Role.tank: tank_emoji,
            Role.healer: healer_emoji,
            Role.dps: dps_emoji,
        }
        # Display main role assignments
        value = self.__get_member_str(role_emoji_dict)
        embed.add_field(
            name=f"Interested:",
            value=value,
            inline=False
        )

        # Changed to use fetch_message and edit
        try:
            # Fetch a fresh message object before editing
            current_message = await message.channel.fetch_message(message.id)
            await current_message.edit(embed=embed)
        except discord.NotFound:
            print("Message not found - it may have been deleted")
        except discord.Forbidden:
            print("Bot doesn't have permission to edit the message")
        except Exception as e:
            print(f"Error updating message: {e}")

    def add_member(self, roles: list[Role], user: Optional[User | Member] = None, user_id: Optional[str] = None):
        _user_id = user_id or user.id
        if _user_id in self.__members:
            for role in roles:
                self.__members[_user_id].add(role)
        else:
            self.__members[_user_id] = set(roles)

    def remove_user(self, user: User | Member) -> tuple[Optional[Role], Optional[str]]:
        self.__members.pop(user.id, None)
        return None, None


    def get_user_role(self, user_id: str) -> tuple[Role, bool]:
        return self.__members.get(user_id, None), False
            

    def send_reminder(self, channel):
        pass