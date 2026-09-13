import discord

from utils.time import utc_now


# =========================
# Base Embed Builder
# =========================


def create_base_embed(
    *,
    title: str | None = None,
    description: str | None = None,
    color: discord.Color | None = None,
) -> discord.Embed:
    """Create a standardized base embed."""

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=utc_now(),
    )

    return embed
