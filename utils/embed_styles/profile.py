import discord

from utils.embed_styles.base import create_base_embed


# =========================
# Profile Colors
# =========================

PROFILE_COLOR = discord.Color.dark_purple()


# =========================
# Profile Embed Builder
# =========================


def profile_embed(
    title: str,
    description: str,
) -> discord.Embed:
    """Create a futuristic profile embed."""

    return create_base_embed(
        title=title,
        description=description,
        color=PROFILE_COLOR,
    )
