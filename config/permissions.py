import discord

from config.settings import BOT_OWNER_ID


def is_bot_owner(user: discord.abc.User) -> bool:
    """Check if the user is the bot developer/owner."""
    return user.id == BOT_OWNER_ID


def is_server_owner(member: discord.Member) -> bool:
    """Check if the user owns the current server."""
    return member.guild.owner_id == member.id


def is_admin(member: discord.Member) -> bool:
    """Check if the user has Administrator permission."""
    return member.guild_permissions.administrator


def is_developer(user: discord.abc.User) -> bool:
    """Alias for checking the bot developer."""
    return is_bot_owner(user)
