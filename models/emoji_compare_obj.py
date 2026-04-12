from typing import Optional

from discord import Emoji, PartialEmoji


class EmojiCompareObj:
    __underly: Emoji | PartialEmoji | str | None
    val: Optional[str]
    id: Optional[int] = None
    type: type

    def __init__(self, emoji: Emoji | PartialEmoji | str | None):
        self.__underly = emoji

        self.type = type(self.__underly)
        if self.type is Emoji:
            self.val = self.__underly.name
            self.id = self.__underly.id
        elif self.type is PartialEmoji:
            self.val = self.__underly.name
            self.id = self.__underly.id
        elif self.type is str:
            self.val = self.__underly
        elif self.__underly is not None:
            raise Exception("unknown value stored for emoji: ", self.__underly)
        
    def __eq__(self, to_compare) -> bool:
        if type(to_compare) is not EmojiCompareObj:
            return False
        
        if self.type is None and to_compare.type is None:
            print("two empty emoji comparers")
            return True
        
        if self.val == to_compare.val:
            if self.id is not None and to_compare.id is not None and self.id != to_compare.id:
                return False
            return True
        
        return False