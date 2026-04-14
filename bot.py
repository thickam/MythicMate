from typing import overload

import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import asyncio
import pytz
from sqlite3 import Error
import db_schema
import bot_emoji
from models.active_group import ActiveGroup
from models.aliased_list import AliasedList
from models.dungeon_group import DungeonGroup
from models.role import Role
from bot_utils import get_mention_str

#region setup
# Load environment variables from .env file
load_dotenv()

# Get the bot token from environment variables
TOKEN = os.getenv('BOT_TOKEN')
# At the start, after load_dotenv()
print(f"Token loaded from environment: {'Yes' if TOKEN else 'No'}")
print(f"Token length: {len(TOKEN) if TOKEN else 0}")

# Configure the bot with the necessary intents (permissions)
intents = discord.Intents.default()
intents.reactions = True
intents.guilds = True
intents.guild_messages = True
intents.message_content = True

print("Intents configured:")
print(f"- Reactions: {intents.reactions}")
print(f"- Guilds: {intents.guilds}")
print(f"- Guild Messages: {intents.guild_messages}")
print(f"- Message Content: {intents.message_content}")

# Initialize the bot with a command prefix and intents
bot = commands.Bot(command_prefix='!', intents=intents)
ActiveGroup.set_client_instance(bot)

background_tasks = set()
def __queue_task(task: asyncio.Task):
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)

# Define the available dungeons and their abbreviations
# This dictionary maps full dungeon names to a list of their common abbreviations or shorthand names
dungeon_aliases = AliasedList({
    "Pit of Saron":["pos", "pit", "saron"],
    "Skyreach":["sky", "sr", "s"],
    "Seat of the Triumvirate":["seat", "sot"],
    "Algeth'ar Academy":["aa", "algethar", "academy", "algethar academy"],
    "Magisters' Terrace":["mt", "magisters terrace", "magister", "magisters"],
    "Maisara Caverns":["mc", "masiara", "cavern", "caverns", "maisara cavern", "trolls"],
    "Nexus-Point Xenas":["npx", "nexus point", "nexus-point", "xenas", "xexus-noint penas"],
    "Windrunner Spire":["wrs", "spire", "windrunner", "wind runner", "wind runner spire"],
    "Any": ["a", "any"]
})

role_aliases = AliasedList({
    "Tank": ["tank", "t"],
    "Healer": ["healer", "h", "heals", "heal"],
    "DPS": ["dps", "damage", "dmg", "dpser", "d"]
})

#endregion

# Event handler for when the bot is ready and connected to Discord
@bot.event
async def on_ready():
    print(f'Bot is ready! Logged in as {bot.user}')
    try:
        sync_routine = bot.tree.sync() # Synchronize the command tree with Discord
        db_schema.initialize_schema_if_missing()
        synced = await sync_routine  
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# Global dictionary to store active groups
active_groups: dict[str, ActiveGroup] = {}

@overload
async def update_group_embed(active_group: ActiveGroup):
    return update_group_embed(active_group.get_message(), active_group.get_embed(), active_group.get_state())

@overload
async def update_group_embed(message: discord.InteractionMessage, embed: discord.Embed, group_state: DungeonGroup):
    """
    Updates the embed message with current group composition and backup information.
    
    Args:
        message: The Discord message to update
        embed: The embed object to modify
        group_state: Current state of the group including members and backups
    """
    if not message or not embed or not group_state:
        print("Missing required parameters for update_group_embed")
        return
        
    try:
        embed.clear_fields()
        
        # Display main role assignments
        embed.add_field(
            name=f"{bot_emoji.get_role_emoji(Role.tank, message.guild)} Tank",
            value=get_mention_str(group_state.get_tank()) if group_state.get_tank() else "None",
            inline=False
        )
        embed.add_field(
            name=f"{bot_emoji.get_role_emoji(Role.healer, message.guild)} Healer",
            value=get_mention_str(group_state.get_healer()) if group_state.members["Healer"] else "None",
            inline=False
        )
        
        # Display DPS slots (filled or empty)
        dps_value = "\n".join([get_mention_str(dps_user) for dps_user in group_state.get_dps()] + ["None"] * (3 - len(group_state.get_dps())))
        embed.add_field(
            name=f"{bot_emoji.get_role_emoji(Role.dps, message.guild)} DPS", 
            value=dps_value, 
            inline=False
        )
        
        # Display backup players for each role
        backup_text = ""
        role: Role
        backups: list[str]
        for role, backups in group_state.get_members_in_backup():
            if backups:
                backup_text += f"\n**{role.value}**: " + ", ".join(get_mention_str(backup) for backup in backups)
        
        if backup_text:
            embed.add_field(name="📋 Backups", value=backup_text.strip(), inline=False)

        # Changed to use fetch_message and edit
        try:
            # Fetch a fresh message object before editing
            current_message = await message.channel.fetch_message(message.id)
            await current_message.edit(embed=embed)
        except discord.NotFound:
            print("Message not found - it may have been deleted")
        except discord.Forbidden:
            print("Bot doesn't have permission to edit the message")
        except Exception as e:
            print(f"Error updating message: {e}")

    except Exception as e:
        print(f"Error in update_group_embed: {e}")

@bot.tree.command(name="lfm", description="Start looking for members for a Mythic+ run.")
@app_commands.describe(
    dungeon="Enter the dungeon name or abbreviation",
    key_level="Enter the key level (e.g., +10)",
    role="Select your role in the group: Tank, Healer, or DPS",
    in_hours="Hours until this run will take place",
    in_minutes="Minutes until this run will take place"
)
async def lfm(interaction: discord.Interaction, dungeon: str, key_level: str, role: str, in_hours: str = '0', in_minutes: str = '0'):
    print(f"LFM command received from {interaction.user}")
    print("Starting LFM command...")
    
    # Validate dungeon name
    
    full_dungeon_name = dungeon_aliases.normalize(dungeon)
    # Validate role name
    full_role_name = role_aliases.normalize(role)
    if not full_dungeon_name:
        await interaction.response.send_message(
            f"Sorry, I couldn't recognize the dungeon name '{dungeon}'. Please try again with a valid name or abbreviation.",
            ephemeral=True
        )
        return
    if not full_role_name:
        await interaction.response.send_message(
            f"Sorry, I couldn't recognize the role '{role}'. Please try again with a valid name or abbreviation.",
            ephemeral=True
        )
        return
    hours_mins_valid = in_hours.isdigit() and in_minutes.isdigit()
    inHours = int(in_hours)
    inMinutes = int(in_minutes)
    hours_mins_valid = hours_mins_valid and inHours >= 0 and inMinutes >= 0
    if not hours_mins_valid:
        await interaction.response.send_message(
            f"Sorry, inMinutes and inHours must both be numbers 0 or greater. Please try again with a valid time offset.",
            ephemeral=True
        )
        return

    # Handle scheduling
    schedule_time = None
    schedule_time_str = None
    if inHours != 0 or inMinutes != 0:
        schedule_time = (datetime.now(timezone.utc) + timedelta(hours=inHours, minutes=inMinutes)).replace(second=0, microsecond=0)
        
        timestamp_int = round(schedule_time.timestamp())
        schedule_str = f"<t:{timestamp_int}:f> (<t:{timestamp_int}:R>)"
    else:
        schedule_str = "now"

    # Initialize group state and create embed
    group_state = DungeonGroup(interaction, full_role_name, schedule_time)
    embed = discord.Embed(
        title=f"Dungeon: {full_dungeon_name}",
        description=f"Difficulty: {key_level}\nScheduled: {schedule_str}",
        color=discord.Color.blue()
    )
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url)
    embed.set_thumbnail(url="https://example.com/path/to/your/image.png")

    # Create and store group message - Changed to use channel.send instead of interaction.followup
    callback = await interaction.response.send_message(embed=embed)
    
    group_message = callback.resource
    active_group = ActiveGroup(group_state, embed, group_message, full_dungeon_name, key_level)
    active_groups[group_message.id] = active_group

    # Update embed with initial group composition
    await update_group_embed(group_message, embed, group_state)

    # Add role selection reactions
    _task_first = None
    _task_previous = None
    for role in Role:
        emoji = bot_emoji.get_role_emoji(role, interaction.guild)
        _task = asyncio.create_task(group_message.add_reaction(emoji))
        if _task_first is None:
            _task_first = _task
        if _task_previous is not None:
            _task_previous.add_done_callback(lambda t: __queue_task(t))
        _task_previous = _task
    __queue_task(_task_first)
    # for emoji in role_emojis.values():
    #     await group_message.add_reaction(emoji)

    # Set up reminder if scheduled for later
    if schedule_time:
        group_state.reminder_task = asyncio.create_task(
            group_state.send_reminder(interaction.channel)
        )

    print(f"Created group message with ID: {group_message.id}")
    print(f"Active groups after creation: {list(active_groups.keys())}")

@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    print(f"Reaction detected - Emoji: {reaction.emoji}, User: {user}, Message ID: {reaction.message.id}")
    if user == bot.user:
        print("Reaction was from bot, ignoring")
        return

    group_info = active_groups.get(reaction.message.id)
    if not group_info:
        print(f"No group found for message ID {reaction.message.id}")
        print(f"Active groups: {list(active_groups.keys())}")
        return

    print(f"Found group info for message {reaction.message.id}")
    group_state = group_info.get_state()
    group_message = group_info.get_message()
    embed = group_info.get_embed()

    # Handle role clearing
    reaction_role = bot_emoji.role_from_emoji(reaction.emoji, reaction.message.guild)
    if reaction_role == Role.clear_role:
        role, promoted_user = group_state.remove_user(user)
        if promoted_user:
            await group_message.channel.send(
                f"{promoted_user.mention} has been promoted from backup to {role}!",
                delete_after=10
            )
        # Remove all role reactions from the user
        for role in Role:
            if role != Role.clear_role:
                emoji = bot_emoji.get_role_emoji(role, reaction.message.guild)
                await group_message.remove_reaction(emoji, user)
        await update_group_embed(group_message, embed, group_state)
        await group_message.remove_reaction(reaction.emoji, user)
        return

    # Prevent users from selecting multiple roles
    current_role = group_state.get_user_role(user)
    if current_role:
        await group_message.remove_reaction(reaction.emoji, user)
        await user.send("You can only select one role. Please remove your current role first.")
        return

    # Handle role selection
    role_added = False
    if(reaction_role != Role.clear_role):
        role_added = group_state.add_member(reaction_role.value, user)

    # Notify user if added to backup
    if not role_added:
        await user.send("You've been added to the backup list for this role.")

    await update_group_embed(group_message, embed, group_state)

    # Add completion marker if group is full
    if group_state.is_complete():
        await group_message.add_reaction("✅")

@bot.event
async def on_reaction_remove(reaction: discord.Reaction, user: discord.Member | discord.User):
    """
    Handles when users remove their role reactions.
    
    Args:
        reaction: The reaction emoji removed
        user: The user who removed the reaction
    """
    if user == bot.user:
        return

    group_info = active_groups.get(reaction.message.id)
    if not group_info:
        return

    group_state: DungeonGroup = group_info.get_state()

    # Remove user from their role
    group_state.remove_user(user)

    await update_group_embed(group_info)

@bot.event
async def on_message(message: discord.Message):
    print(f"Message received: {message.content[:20]}...")
    await bot.process_commands(message)

# Run the bot with the token loaded from the environment variables
bot.run(TOKEN)
