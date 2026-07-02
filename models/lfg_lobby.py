import asyncio
import traceback
from typing import Callable

import discord
from discord.abc import GuildChannel, PrivateChannel

import bot_emoji
from bot_utils import get_mention_str
from models.lfg_user import LfgUser
from models.role import Role

class LfgLobby:
    SCALAR_HOURS: int = 3600
    SCALAR_MINUTES: int = 60
    TIME_SCALE: int = SCALAR_MINUTES

    def __init__(self, bot: discord.Client, channel_id: int):
        self.__active_user_lock = asyncio.Lock()
        self.__scheduled_user_lock = asyncio.Lock()
        self.__active_users: list[LfgUser] = []
        self.__scheduled_users: list[LfgUser] = []
        self.__task_list: list[asyncio.Task] = []
        self.__message_update_task: asyncio.Task | None = None
        self.__message_id: int | None = None
        self.__bot_ref = bot
        self.__channel_id = channel_id

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
        
    async def __move_user_async(self, user: LfgUser, in_hours: int):
        asyncio.sleep(max(in_hours * self.TIME_SCALE, 5))
        async with self.__scheduled_user_lock:
            if user in self.__scheduled_users:
                self.__scheduled_users.remove(user)
        async with self.__active_user_lock:
            self.__active_users.append(user)
        await self.update_lfg_message()

    async def __schedule_user(self, user: LfgUser, in_hours: int):
        async with self.__scheduled_user_lock:
            self.__scheduled_users.append(user)
        task = asyncio.create_task(self.__move_user_async(user, in_hours), user.get_user_id())
        self.__task_list.append(task)

    async def unschedule_user(self, user_id: str):
        for task in self.__task_list:
            if task.get_name() == user_id:
                task.cancel()
                break
            
        async with self.__scheduled_user_lock:
            user_to_unschedule = None
            for user in self.__scheduled_users:
                user_to_unschedule = user if user.has_id(user_id) else None
            if user_to_unschedule:
                self.__scheduled_users.remove(user)

    def __determine_roles(self, role_str: str) -> list[Role]:
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
    
    async def __remove_inactive_user(self, user_id: str, in_hours: int):
        asyncio.sleep(max(self.TIME_SCALE * in_hours), 5)
        async with self.__scheduled_user_lock:
            user_index = -1
            for user, index in self.__scheduled_users:
                if user.has_id(user_id):
                    user_index = index
                    break
            if user_index > -1:
                self.__scheduled_users.pop(user_index)
        await self.update_lfg_message()

    async def add_user(self, user_id: str, key_level_range: str, role_str: str, for_hours: str, in_hours: str | None):
        # if already active or scheduled, remove them
        if await self.__is_active_user(user_id):
            await self.remove_active_user(user_id)
        if user_id in self.__scheduled_users:
            await self.unschedule_user(user_id)

        roles = self.__determine_roles(role_str)
        new_user = LfgUser(user_id, roles, key_level_range)

        parsed_in_hours = self.__parse_hours_str(in_hours)
        parsed_for_hours = self.__parse_hours_str(for_hours)

        calculated_for_hours = for_hours
        if parsed_in_hours:
            await self.__schedule_user(new_user, parsed_in_hours)
            # Need to add in_hours to for_hours so it removes them in for_hours AFTER they start (in in_hours hours)
            calculated_for_hours = calculated_for_hours + in_hours
        else:
            async with self.__active_user_lock:
                self.__active_users.append(new_user)
            await self.update_lfg_message()

        if parsed_for_hours:
            asyncio.create_task(self.__remove_inactive_user(user_id, calculated_for_hours))
        
    async def remove_active_user(self, user_id: str):
        async with self.__active_user_lock:
            self.__active_users = [user for user in self.__active_users if not user.has_id(user_id)]
        await self.update_lfg_message()

    async def __get_member_str(self, role_emoji_dict: dict[Role, discord.Emoji | discord.PartialEmoji | str | None]) -> str :
        individual_member_strings = []
        async with self.__active_user_lock:
            print("active user lock acquired")
            for lfg_user in self.__active_users:
                individual_member_strings.append(get_mention_str(lfg_user.get_user_id()))
                # print("Appending user to list: ", str(lfg_user.get_user_id()))
                # emoji_list = " ".join(str(role_emoji_dict[role]) for role in lfg_user.get_roles())
                # individual_str = f"{get_mention_str(lfg_user.get_user_id())} - {emoji_list}"
                # individual_member_strings.append(individual_str)
        return "\n".join(individual_member_strings) if individual_member_strings else "Nobody yet..."

    async def __create_lfg_embed(self, bot: discord.Client, file: discord.File | None, guild: discord.Guild) -> discord.Embed:
        embed = discord.Embed(
            title=f"M+ Lobby",
            color=discord.Color.green()
        )

        tank_emoji = bot_emoji.get_role_emoji(Role.tank, guild)
        healer_emoji = bot_emoji.get_role_emoji(Role.healer, guild)
        dps_emoji = bot_emoji.get_role_emoji(Role.dps, guild)
        role_emoji_dict: dict[Role, discord.Emoji | discord.PartialEmoji | str | None] = {
            Role.tank: tank_emoji,
            Role.healer: healer_emoji,
            Role.dps: dps_emoji,
        }

        value = await self.__get_member_str(role_emoji_dict)
        embed.add_field(
            name=None, 
            value=value, 
            inline=False
        )

        embed.set_author(name=bot.user.display_name, icon_url=f"attachment://{file.filename}" if file else None)
        return embed

    async def __update_lfg_message(self, bot: discord.Client, channel: discord.TextChannel | GuildChannel | PrivateChannel | discord.PartialMessageable):
        async with self.__active_user_lock:
            if self.__message_id:
                try:
                    old_message = await channel.fetch_message(self.__message_id)
                    await old_message.delete()
                
                except discord.NotFound:
                    print("No old message found")
                except Exception as e:
                    traceback.print_tb(e)
                    print(e)
            file = None
            try:
                file = discord.File("./resources/BnetLfgEye.PNG", filename="BnetLfgEye.png")
            except:
                pass
            lfg_embed = await self.__create_lfg_embed(bot, file, channel.guild)
            message = await channel.send(embed=lfg_embed, silent=True, file=file)
            self.__message_id = message.id

    def __should_cancel_update_task(self) -> bool:
        return self.__message_update_task\
        and not self.__message_update_task.done()\
        and not self.__message_update_task.cancelled()\
        and not self.__message_update_task.cancelling()
    
    async def __remove_update_task_ref(self):
        if self.__should_cancel_update_task:
            self.__message_update_task.cancel()
        self.__message_update_task = None
            
    async def update_lfg_message(self):
        if self.__should_cancel_update_task():
            self.__message_update_task.cancel()
        channel = self.__bot_ref.get_channel(self.__channel_id)
        self.__message_update_task = asyncio.create_task(self.__update_lfg_message(self.__bot_ref, channel))
        # self.__message_update_task.add_done_callback(self.__remove_update_task_ref())
