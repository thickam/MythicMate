
class AliasedList():
    __alias_dict: dict[str, list[str]]
    __alias_lookup: dict[str, str]

    def get_alias_dict(self) -> dict[str, list[str]]:
        return self.__alias_dict

    def __init__(self, alias_dict: dict[str, list[str]]):
        self.__alias_dict = alias_dict
        self.__build_alias_lookup()

    def __build_alias_lookup(self):
        self.__alias_lookup = dict()
        for full_name, aliases in self.get_alias_dict().items():
            for alias in aliases + [full_name.lower()]:
                self.__alias_lookup[alias] = full_name

    def normalize(self, user_input):
        return self.__alias_lookup.get(user_input.lower())