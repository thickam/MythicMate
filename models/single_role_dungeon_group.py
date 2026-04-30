import asyncio
from datetime import datetime, timezone
from typing import Optional

from discord import Embed, Forbidden, Interaction, InteractionMessage, Member, User
from discord.interactions import InteractionChannel

import bot_emoji
from bot_utils import get_mention_str
from models.dungeon_group import DungeonGroup
from models.role import Role


class SingleRoleDungeonGroup(DungeonGroup):
    """
    Manages the state of a Mythic+ group including members, backups, and reminders.
    
    Attributes:
        members: Dictionary containing current group members by role
        backups: Dictionary containing backup players by role
        reminder_task: Optional asyncio task for scheduled groups
    """

    def __init__(self, interaction: Interaction, initial_role: Role, schedule_time:Optional[datetime]=None):
        """
        Initializes a new group state.
        
        Args:
            interaction: Discord interaction that created the group
            initial_role: Starting role of the group creator
            schedule_time: Optional datetime for scheduled groups
        """
        self.__members: dict[Role, str | list[str] | None] = {
            Role.tank: None,
            Role.healer: None,
            Role.dps: []
        }

        self.__backups: dict[Role, list[str]] = {
            Role.tank: [],
            Role.healer: [],
            Role.dps: []
        }

        self.__flex: dict[Role, list[str]] = {
            Role.tank: [],
            Role.healer: [],
            Role.dps: []
        }

        self.schedule_time = schedule_time
        self.reminder_task: Optional[asyncio.Task] = None
        
        # Add the command user to their selected role
        user = interaction.user
        self.add_member(initial_role, user=user)
    
    def get_members_in_backup(self, role: Optional[Role] = None):
        if role is None:
            return self.__backups
        else:
            return self.__backups.get(role)
            
    def get_tank(self) -> str:
        return self.__members.get(Role.tank)
            
    def get_healer(self) -> str:
        return self.__members.get(Role.healer)
            
    def get_dps(self) -> list[str]:
        return self.__members.get(Role.dps)
        
    def add_member(self, role: Role, user: Optional[User | Member] = None, user_id: Optional[str] = None):
        _user_id: str = None
        if user is not None:
            _user_id = user.id
        elif user_id is not None:
            _user_id = user_id
        else:
            raise Exception("Need to pass one of user or user_id to DungeonGroup::__add_member")
        if self.has_room_for(role):
            match role:
                case Role.tank | Role.healer:
                    self.__members[role] = _user_id
                case Role.dps:
                    self.__members[role].append(_user_id)
                case _:
                    print(f"Invalid member attempting to join group as {role.value}")
                    return False
            return True
        else:
            self.__backups[role].append(_user_id)
            return False
    
    def has_room_for(self, role: Role) -> bool:
        match role:
            case Role.tank | Role.healer:
                return self.__members[role] is None
            case Role.dps:
                return len(self.__members[role]) < 3
            case _:
                print(f"Invalid member attempting to join group as {role.value}")
                return False

    def __remove_user_from_role(self, role: Role, user: User | Member | None = None, user_id: str | None = None):
        if user is None and user_id is None:
            raise Exception("Must supply user or user_id to remove user from role")
        _user_id = user_id or user.id
        if role == Role.tank or role == Role.healer:
            if self.__members[role] != _user_id:
                print(f"Attempted to remove {user_id} from role {role.value} but was not found")
                raise Exception("Attempted to remove someone from group that was not in expected role")
            self.__members[role] = None
        elif role == Role.dps:
            self.__members[role].remove(_user_id)
        else:
            raise Exception(f"Attempted to remove user from invalid role: {role.name} ({role.value})")

    def remove_user(self, user: User | Member) -> tuple[Optional[Role], Optional[str]]:
        """
        Removes a user from their role and promotes a backup if available.
        
        Args:
            user: The Discord user to remove
            
        Returns:
            tuple: (role_removed_from, promoted_user) or (None, None) if user not found
        """
        # Check main roles first
        user_role, is_backup = self.get_user_role(user.id)

        if is_backup:
            for role, backup_list in self.__backups.items():
                if user in backup_list:
                    backup_list.remove(user)
                    return role, None
        else:
            self.__remove_user_from_role(user_role, user_id = user.id)
            if self.__backups[user_role]:
                user_to_promote = self.__backups[user_role].pop(0)
                self.add_member(user_role, user_id=user_to_promote)
                return user_role, user_to_promote
            return user_role, None
        return None, None

    def get_user_role(self, user_id: str) -> tuple[Role, bool]:
        """
        Gets the current role of a user in the group.
        
        Args:
            user: The Discord user to check
            
        Returns:
            str: The user's role or None if not in group
        """
        role = None
        is_backup = False
        if self.get_tank() == user_id:
            role = Role.tank
        elif self.get_healer() == user_id:
            role = Role.healer
        elif user_id in self.get_dps():
            role = Role.dps
        
        # Check backups
        for _role, backup_list in self.__backups.items():
            if user_id in backup_list:
                role = _role
                is_backup = True
        return role, is_backup

    def is_complete(self) -> bool:
        """
        Checks if the group has all required roles filled.
        
        Returns:
            bool: True if group is complete, False otherwise
        """
        return (
            self.__members[Role.tank] is not None and
            self.__members[Role.healer] is not None and
            len(self.__members[Role.dps]) == 3
        )

    async def send_reminder(self, channel: InteractionChannel | None):
        """
        Sends reminders to group members before scheduled start time.
        
        Args:
            channel: The Discord channel to send fallback messages to
        """
        if not self.reminder_task:
            return

        try:
            # Wait until 15 minutes before scheduled time
            await asyncio.sleep(max(0, (self.schedule_time - datetime.now(timezone.utc)).total_seconds() - 900))
            
            # Send DMs to all members
            all_members = [
                self.__members["Tank"],
                self.__members["Healer"],
                *self.__members["DPS"]
            ]
            
            for member in all_members:
                if member:
                    try:
                        await member.send(f"Reminder: Your M+ run starts in 15 minutes!")
                    except Forbidden:
                        await channel.send(
                            f"{member.mention} (Could not send DM: Your M+ run starts in 15 minutes!)",
                            delete_after=60
                        )
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in reminder task: {e}")

    async def update_group_embed(self, message: InteractionMessage, embed: Embed):
        """
        Updates the embed message with current group composition and backup information.
        
        Args:
            message: The Discord message to update
            embed: The embed object to modify
            group_state: Current state of the group including members and backups
        """
        if not message or not embed:
            print("Missing required parameters for update_group_embed")
            return
            
        embed.clear_fields()
        
        # Display main role assignments
        embed.add_field(
            name=f"{bot_emoji.get_role_emoji(Role.tank, message.guild)} Tank",
            value=get_mention_str(self.get_tank()) if self.get_tank() else "None",
            inline=False
        )
        embed.add_field(
            name=f"{bot_emoji.get_role_emoji(Role.healer, message.guild)} Healer",
            value=get_mention_str(self.get_healer()) if self.get_healer() else "None",
            inline=False
        )
        
        # Display DPS slots (filled or empty)
        dps_value = "\n".join([get_mention_str(dps_user) for dps_user in self.get_dps()] + ["None"] * (3 - len(self.get_dps())))
        embed.add_field(
            name=f"{bot_emoji.get_role_emoji(Role.dps, message.guild)} DPS", 
            value=dps_value, 
            inline=False
        )
