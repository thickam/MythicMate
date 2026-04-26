import asyncio
from typing import Callable

from models.lfg_user import LfgUser
from models.role import Role

class LfgLobby:
    def __init__(self):
        self.__active_user_lock = asyncio.Lock()
        self.__scheduled_user_lock = asyncio.Lock()
        self.__active_users: list[LfgUser] = []
        self.__scheduled_users: list[LfgUser] = []
        self.__task_list = []

    @classmethod
    def __parse_hours_str(cls, hours: str) -> int | None:
        if not hours:
            return None
        return int(hours)

    def __user_in_list(self, user_id: str, user_list: list[LfgUser]):
        for user in user_list:
            if user.has_id(user_id):
                return True
        return False

    async def __is_active_user(self, user_id: str):
        async with self.__active_user_lock:
            return self.__user_in_list(user_id, self.__active_users)

    async def __is_scheduled_user(self, user_id: str):
        async with self.__scheduled_user_lock:
            return self.__user_in_list(user_id, self.__scheduled_users)

    def unschedule_user(self, user_id: str):
        pass

    def __determine_roles(role_str: str) -> list[Role]:
        result = []
        for role_character in role_str:
            match role_character:
                case 't':
                    result.append(Role.tank)
                case 'h':
                    result.append(Role.healer)
                case 'd':
                    result.append(Role.dps)
                case _:
                    print(f"Invalid role selection: '{role_character}'")
        return result

    def add_user(self, user_id: str, key_level_range: str, role_str: str, for_hours: str, in_hours: str | None):
        # if already active or scheduled, remove them
        if self.__is_active_user(user_id):
            self.remove_active_user(user_id)
        if user_id in self.__scheduled_users:
            self.unschedule_user(user_id)

        roles = self.__determine_roles(role_str)
        new_user = LfgUser(user_id, roles, key_level_range)

        parsed_in_hours = self.__parse_hours_str(in_hours)
        parsed_for_hours = self.__parse_hours_str(for_hours)

        if parsed_in_hours:
            self.__scheduled_users.append(new_user)
        else:
            self.__active_users.append(new_user)

        if parsed_for_hours:
            pass

        
    def remove_active_user(self, user_id: str):
        self.__active_users = [user for user in self.__active_users if not user.has_id(user_id)]
        
