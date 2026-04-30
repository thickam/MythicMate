from typing import Optional

from discord import Client, Embed, InteractionMessage, PartialMessage, Thread
from discord.abc import GuildChannel, PrivateChannel

from models.dungeon_group import DungeonGroup

class ActiveGroup:
    __client: Client
    @classmethod
    def set_client_instance(cls, client: Client):
        cls.__client = client

    @classmethod
    def get_client_instance(cls) -> Client:
        return cls.__client

    def __init__(self, state: DungeonGroup, embed: Embed, message: InteractionMessage, dungeon: str, key_level: str):
        self.__embed_id: str
        self.__embed: Embed | None
        self.__message_channel: GuildChannel | PrivateChannel | Thread | None
        self.__message_channel_id: str
        self.__message_id: str
        self.__message: Optional[InteractionMessage]

        self.__state: DungeonGroup = state
        self.set_embed(embed=embed)
        self.set_message(message=message)
        self.dungeon: str = dungeon
        self.key_level: str = key_level

    def get_state(self) -> DungeonGroup:
        return self.__state

    def get_embed_id(self) -> str:
        return self.__embed_id

    def get_embed(self) -> Optional[Embed]:
        if self.__embed is None:
            self.__hydrate_embed()
        return self.__embed
    
    def set_embed(self, embed: Optional[Embed] = None, embed_id: Optional[str] = None, and_hydrate: bool = False):
        self.__embed = None
        if embed is not None:
            self.__embed_id = embed.url
            self.__embed = embed
        elif embed_id is not None:
            self.__embed_id = embed_id
            if and_hydrate:
                ActiveGroup.get_client_instance().fetch_channel()
                self.__hydrate_embed()
        return self.__embed
    
    def get_message_id(self):
        return self.__message_id

    def get_message(self):
        if self.__message is None:
            self.__hydrate_message()
        return self.__message

    def set_message(self, message: Optional[InteractionMessage] = None, message_id: Optional[str] = None, channel_id: Optional[str] = None, andHydrate: bool = False):
        self.__message = None
        self.__message_id = None
        self.__message_channel = None
        self.__message_channel_id = None
        if message is not None:
            self.__message = message
            self.__message_id = str(message.id)
            self.__message_channel = message.channel
            self.__message_channel_id = str(message.channel.id)
        elif message_id is not None and channel_id is not None:
            self.__message_id = message_id
            self.__message_channel_id = channel_id
            # Invalidate message & channel references that could technically be stale (channel should never go stale but idk)
            self.__message = None
            self.__message_channel = None
            if andHydrate:
                return self.get_message()
        return self.__message
    
    def __hydrate_message(self):
        self.__message_channel = ActiveGroup.get_client_instance().get_channel(self.__message_channel_id)
        self.__message = self.__message_channel.get_partial_message(self.__message_id)

    def __hydrate_embed(self):
        msg = self.get_message()
        self.__set_embed(embed=msg.embeds[0])
