import datetime

import discord


# =========================
# Immunity Checks
# =========================


def is_server_owner_target(member: discord.Member) -> bool:
    """Check whether a member is the owner of their server."""

    return member.id == member.guild.owner_id


def can_moderate(
    moderator: discord.Member,
    target: discord.Member,
) -> bool:
    """Check whether the moderator's top role outranks the target's."""

    if is_server_owner_target(target):
        return False

    return moderator.top_role > target.top_role


def can_bot_moderate(
    bot_member: discord.Member,
    target: discord.Member,
) -> bool:
    """Check whether the bot's top role outranks the target's."""

    if is_server_owner_target(target):
        return False

    return bot_member.top_role > target.top_role


# =========================
# Direct Message Notifications
# =========================


async def notify_member(
    member: discord.Member,
    embed: discord.Embed,
) -> bool:
    """Attempt to DM a member about a moderation action. Never raises."""

    try:
        await member.send(embed=embed)
        return True
    except (discord.Forbidden, discord.HTTPException):
        return False


# =========================
# Moderation Actions
# =========================


async def apply_timeout(
    member: discord.Member,
    seconds: int,
    reason: str | None = None,
):
    """Timeout a member. Returns (success, error)."""

    try:
        await member.timeout(
            datetime.timedelta(seconds=seconds),
            reason=reason,
        )
        return True, None
    except discord.Forbidden:
        return False, "forbidden"
    except discord.HTTPException:
        return False, "http_error"


async def apply_kick(
    member: discord.Member,
    reason: str | None = None,
):
    """Kick a member. Returns (success, error)."""

    try:
        await member.kick(reason=reason)
        return True, None
    except discord.Forbidden:
        return False, "forbidden"
    except discord.HTTPException:
        return False, "http_error"


async def apply_ban(
    member: discord.Member,
    reason: str | None = None,
    delete_message_seconds: int = 0,
):
    """Ban a member. Returns (success, error)."""

    try:
        await member.ban(
            reason=reason,
            delete_message_seconds=delete_message_seconds,
        )
        return True, None
    except discord.Forbidden:
        return False, "forbidden"
    except discord.HTTPException:
        return False, "http_error"


async def remove_timeout(
    member: discord.Member,
    reason: str | None = None,
):
    """Remove an active timeout from a member. Returns (success, error)."""

    try:
        await member.timeout(None, reason=reason)
        return True, None
    except discord.Forbidden:
        return False, "forbidden"
    except discord.HTTPException:
        return False, "http_error"
