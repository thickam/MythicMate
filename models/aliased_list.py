
class AliasedList():
    __alias_dict: dict[str, list[str]]
    __alias_lookup: dict[str, str]

    def get_alias_dict(self) -> dict[str, list[str]]:
        return self.__alias_dict

    dungeon_aliases = {
    "Pit of Saron":["pos", "pit", "saron"],
    "Skyreach":["sky", "sr", "s"],
    "Seat of the Triumvirate":["seat", "sot"],
    "Algeth'ar Academy":["aa", "algethar", "academy", "algethar academy"],
    "Magisters' Terrace":["mt", "magisters terrace", "magister", "magisters"],
    "Maisara Caverns":["mc", "masiara", "cavern", "caverns", "maisara cavern", "trolls"],
    "Nexus-Point Xenas":["npx", "nexus point", "nexus-point", "xenas", "xexus-noint penas"],
    "Windrunner Spire":["wrs", "spire", "windrunner", "wind runner", "wind runner spire"],
    "Any": ["a", "any"]
    }

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