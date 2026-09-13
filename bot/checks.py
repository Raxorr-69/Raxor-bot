from discord.ext import commands

from config.permissions import (
    is_bot_owner,
    is_server_owner,
    is_admin,
)


# =========================
# Developer Check
# =========================

def developer_only():
    """Allow only the bot developer to use the command."""
    
    async def predicate(ctx: commands.Context) -> bool:
        return is_bot_owner(ctx.author)

    return commands.check(predicate)


# =========================
# Server Owner Check
# =========================

def server_owner_only():
    """Allow only the server owner to use the command."""
    
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.guild is None:
            return False

        return is_server_owner(ctx.author)

    return commands.check(predicate)


# =========================
# Admin Check
# =========================

def admin_only():
    """Allow only administrators to use the command."""
    
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.guild is None:
            return False

        return is_admin(ctx.author)

    return commands.check(predicate)
