import asyncio
from datetime import datetime, timezone
from typing import Optional, overload

from discord import Forbidden, Interaction, Member, User

from models.role import Role


class DungeonGroup:
    """
    Manages the state of a Mythic+ group including members, backups, and reminders.
    
    Attributes:
        members: Dictionary containing current group members by role
        backups: Dictionary containing backup players by role
        reminder_task: Optional asyncio task for scheduled groups
    """

    __members: dict[Role, str | list[str] | None] = {
        Role.tank: None,
        Role.healer: None,
        Role.dps: []
    }

    __backups: dict[Role, list[str]] = {
        Role.tank: [],
        Role.healer: [],
        Role.dps: []
    }
    reminder_task: Optional[asyncio.Task] = None
    schedule_time: Optional[datetime]

    def __init__(self, interaction: Interaction, initial_role: Role, schedule_time:Optional[datetime]=None):
        """
        Initializes a new group state.
        
        Args:
            interaction: Discord interaction that created the group
            initial_role: Starting role of the group creator
            schedule_time: Optional datetime for scheduled groups
        """
        self.schedule_time = schedule_time
        
        # Add the command user to their selected role
        user = interaction.user
        self.add_member(initial_role, user)

    def get_members_in_role(self, role: Role) -> list[str]:
        match role:
            case Role.tank | Role.healer:
                return [self.__members.get(role)]
            case Role.dps:
                return self.__members.get(role)
            case _:
                return []

    @overload    
    def get_members_in_backup(self) -> dict[Role, list[str]]:
        return self.__backups
    
    @overload    
    def get_members_in_backup(self, role: Role) -> list[str]:
        return self.__backups.get(role)
            
    def get_tank(self) -> str:
        return self.__members.get(Role.tank)
            
    def get_healer(self) -> str:
        return self.__members.get(Role.healer)
            
    def get_dps(self) -> list[str]:
        return self.__members.get(Role.dps)
        
    @overload
    def add_member(self, role: Role, user: User | Member) -> bool:
        """
        Adds a user to a role, or to backup if role is full.
        
        Args:
            role: The role to add the user to
            user: The Discord user to add
            
        Returns:
            bool: True if added to main role, False if added to backup
        """

        return self.add_member(role, user.id)

    @overload
    def add_member(self, role: Role, user_id: str) -> bool:
        """
        Adds a user to a role, or to backup if role is full.
        
        Args:
            role: The role to add the user to
            user: The ID of a Discord user to add
            
        Returns:
            bool: True if added to main role, False if added to backup
        """

        if self.has_room_for(role):
            match role:
                case Role.tank | Role.healer:
                    self.__members[role] = user_id
                case Role.dps:
                    self.__members[role].append(user_id)
                case _:
                    print(f"Invalid member attempting to join group as {role.value}")
                    return False
            return True
        else:
            self.__backups[role].append(user_id)
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
                self.add_member(user_role, user_to_promote)
                return user_role, user_to_promote
            return user_role, None

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
        if self.__members[Role.tank] == user_id:
            role = Role.tank
        elif self.__members[Role.healer] == user_id:
            role = Role.healer
        elif user_id in self.__members[Role.dps]:
            role = Role.dps
        
        # Check backups
        for _role, backup_list in self.__backups.items():
            if user_id in backup_list:
                role = _role
                is_backup = True
        return role, is_backup

    def is_complete(self):
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

    async def send_reminder(self, channel):
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