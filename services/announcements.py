import discord


# =========================
# Announcement Channel Resolution
# =========================


def resolve_announcement_channel(
    guild: discord.Guild,
    channel_id: int | None,
) -> discord.TextChannel | None:
    """Resolve a stored announcement channel ID to a text channel."""

    if channel_id is None:
        return None

    channel = guild.get_channel(channel_id)

    if not isinstance(channel, discord.TextChannel):
        return None

    return channel


# =========================
# Announcement Delivery
# =========================


async def send_announcement(
    channel: discord.TextChannel,
    embed: discord.Embed,
):
    """Send an announcement embed to a channel. Returns (success, error)."""

    try:
        await channel.send(embed=embed)
        return True, None
    except discord.Forbidden:
        return False, "forbidden"
    except discord.HTTPException:
        return False, "http_error"


async def broadcast_announcement(
    guilds,
    channel_id_getter,
    embed: discord.Embed,
):
    """Send an announcement embed to many servers at once.

    `channel_id_getter` is an async callable that takes a guild ID and
    returns the announcement_channel_id configured for that server.
    """

    results = {}

    for guild in guilds:
        channel_id = await channel_id_getter(guild.id)

        channel = resolve_announcement_channel(guild, channel_id)

        if channel is None:
            results[guild.id] = (False, "no_channel")
            continue

        results[guild.id] = await send_announcement(channel, embed)

    return results
