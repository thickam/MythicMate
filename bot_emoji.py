import os

import discord

from models.emoji_compare_obj import EmojiCompareObj
from models.role import Role

__default_role_emoji = {
    Role.tank: "🛡️",
    Role.healer: "💚",
    Role.dps: "⚔️",
    Role.clear_role: "❌"
}

__zion_role_emoji_names: dict[Role, str] = {
    Role.tank: "tank",
    Role.healer: "heal",
    Role.dps: "dps",
    Role.clear_role: "not"
}

__tnt_role_emoji_names: dict[Role, str] = { # these are for a test
    Role.tank: "minivan",
    Role.healer: "mlem",
    Role.dps: "heck",
    Role.clear_role: "DaleWave2"
}

__GUILD_ID_TNT = os.getenv('GUILD_ID_TNT') and int(os.getenv('GUILD_ID_TNT'))
__GUILD_ID_ZION = os.getenv('GUILD_ID_ZION') and int(os.getenv('GUILD_ID_ZION'))
__guild_role_emoji_dict: dict[int, dict[Role, str]] = {
    __GUILD_ID_TNT: __tnt_role_emoji_names,
    __GUILD_ID_ZION: __zion_role_emoji_names, 
}

__emoji_cache: dict[int, dict[Role, None | discord.Emoji | discord.PartialEmoji | str]] = {
    __GUILD_ID_TNT: {
        Role.tank: None,
        Role.healer: None,
        Role.dps: None,
        Role.clear_role: None
    },
    __GUILD_ID_ZION: {
        Role.tank: None,
        Role.healer: None,
        Role.dps: None,
        Role.clear_role: None
    }
}

def get_role_emoji(role: Role, guild: discord.Guild):
    guild_id = guild.id
    
    if(__emoji_cache.get(guild_id, __default_role_emoji) is None):
        role_emoji_dict = __guild_role_emoji_dict[guild_id]
        guild_specific_emoji = discord.utils.get(guild.emojis, name=role_emoji_dict[role])
        __emoji_cache[guild_id][role] = guild_specific_emoji or __default_role_emoji[role]
    return __emoji_cache\
        .get(guild_id, __default_role_emoji)\
        .get(role)

def is_same_emoji(a: discord.Emoji | discord.PartialEmoji | str, b: discord.Emoji | discord.PartialEmoji | str) -> bool:
    a_comparer = EmojiCompareObj(a)
    b_comparer = EmojiCompareObj(b)

    return a_comparer == b_comparer

def role_from_emoji(emoji: discord.Emoji | discord.PartialEmoji | str, guild: discord.Guild) -> Role | None:
    for role in Role:
        role_emoji = get_role_emoji(role, guild)
        if is_same_emoji(role_emoji, emoji):
            return role

    return None

