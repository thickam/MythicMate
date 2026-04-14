from typing import Optional, overload

from discord import Embed, InteractionMessage, PartialMessage, Thread
from discord.abc import GuildChannel, PrivateChannel
from discord.client import Bot

from models.dungeon_group import DungeonGroup

class ActiveGroup:
    __client: Bot
    @classmethod
    def set_client_instance(cls, client: Bot):
        cls.__client = client

    @classmethod
    def get_client_instance(cls) -> Bot:
        return cls.__client

    __state: DungeonGroup
    __embed_id: str
    __embed: Optional[Embed]
    __message_channel: Optional[GuildChannel | PrivateChannel | Thread]
    __message_channel_id: str
    __message_id: str
    __message: Optional[InteractionMessage]
    dungeon: str
    key_level: str

    def __init__(self, state: DungeonGroup, embed: Embed, message: InteractionMessage, dungeon: str, key_level: str):
        self.__state = state
        self.setEmbed(embed)
        self.set_message(message)
        self.dungeon = dungeon
        self.key_level = key_level

    def get_state(self) -> DungeonGroup:
        return self.__state

    def get_embed_id(self) -> str:
        return self.__embed_id

    def get_embed(self) -> Optional[Embed]:
        if self.__embed is None:
            self.__hydrate_embed()
        return self.__embed
    
    @overload
    def set_embed(self, embed: Embed):
        self.__embed_id = embed.url
        self.__embed = embed

    @overload
    def setEmbed(self, embed_id: str, andHydrate: bool = False) -> Optional[Embed]:
        self.__embed_id = embed_id
        if andHydrate:
            ActiveGroup.get_client_instance().fetch_channel()
            return self.get_embed()
        return None
    
    def get_message_id(self):
        return self.__message_id

    def get_message(self):
        if self.__message is None:
            self.__hydrate_message()
        return self.__message

    @overload
    def set_message(self, message: InteractionMessage):
        self.__message = message
        self.__message_id = str(message.id)
        self.__message_channel = message.channel
        self.__message_channel_id = str(message.channel.id)

    @overload
    def set_message(self, message_id: str, channel_id: str, andHydrate: bool = False) -> Optional[InteractionMessage | PartialMessage]:
        self.__message_id = message_id
        self.__message_channel_id = channel_id
        # Invalidate message & channel references that could technically be stale (channel should never go stale but idk)
        self.__message = None
        self.__message_channel = None
        if andHydrate:
            return self.get_message()
        return None
    
    def __hydrate_message(self):
        self.__message_channel = ActiveGroup.get_client_instance().get_channel(self.__message_channel_id)
        self.__message = self.__message_channel.get_partial_message(self.__message_id)

    def __hydrate_embed(self):
        msg = self.get_message()
        self.set_embed(msg.embeds[0])
