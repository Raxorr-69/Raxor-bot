import discord

from utils.embed_styles.base import create_base_embed


# =========================
# RAXOR NORMAL / BOT UI
# =========================

NORMAL_COLOR = discord.Color(0x8B3DFF)


def normal_embed(
    title: str,
    description: str,
) -> discord.Embed:
    """Create the standard RAXOR bot interface embed."""

    return create_base_embed(
        title=f"› RAXOR // {title}",
        description=description,
        color=NORMAL_COLOR,
    )
