from models.role import Role


class LfgUser:
    def __init__(self, user_id: str, roles: list[Role], key_range: str):
        self.__user_id = user_id
        self.__roles = roles or []
        self.__key_range = key_range

    def has_id(self, user_id: str):
        return self.get_user_id() == user_id
    
    def get_roles(self) -> list[Role]:
        return self.__roles
    
    def has_role(self, role: Role) -> bool:
        return role in self.__roles or len(self.__roles) == 0

    def get_user_id(self) -> str:
        return self.__user_id
    
    def get_key_range(self) -> str:
        return self.__key_range