import discord

from database.repositories import set_inviter


# =========================
# Invite Cache
# =========================

guild_invite_cache = {}


# =========================
# Cache Population
# =========================


async def cache_guild_invites(guild: discord.Guild):
    """Fetch and store the current invite uses for a server."""

    try:
        invites = await guild.invites()
    except (discord.Forbidden, discord.HTTPException):
        return

    guild_invite_cache[guild.id] = {
        invite.code: invite.uses or 0
        for invite in invites
    }


def clear_guild_invites(guild_id: int):
    """Remove a server's cached invites."""

    guild_invite_cache.pop(guild_id, None)


# =========================
# Used Invite Detection
# =========================


async def find_used_invite(
    guild: discord.Guild,
) -> discord.Invite | None:
    """Find the invite whose use count increased since the last cache."""

    cached_uses = guild_invite_cache.get(guild.id, {})

    try:
        current_invites = await guild.invites()
    except (discord.Forbidden, discord.HTTPException):
        return None

    used_invite = None

    for invite in current_invites:
        previous_uses = cached_uses.get(invite.code, 0)

        if (invite.uses or 0) > previous_uses:
            used_invite = invite
            break

    # Refresh the cache for the next join
    guild_invite_cache[guild.id] = {
        invite.code: invite.uses or 0
        for invite in current_invites
    }

    return used_invite


# =========================
# Inviter Tracking
# =========================


async def track_member_invite(
    pool,
    member: discord.Member,
):
    """Resolve and store who invited a new member."""

    used_invite = await find_used_invite(member.guild)

    inviter_id = (
        used_invite.inviter.id
        if used_invite and used_invite.inviter
        else None
    )

    await set_inviter(
        pool,
        guild_id=member.guild.id,
        user_id=member.id,
        inviter_id=inviter_id,
    )

    return inviter_id
