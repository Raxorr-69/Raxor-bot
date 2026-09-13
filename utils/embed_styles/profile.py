import discord

from utils.embed_styles.base import create_base_embed


# =========================
# RAXOR USER PROFILE
# =========================

PROFILE_COLOR = discord.Color(0x8B3DFF)


def profile_embed(
    title: str,
    description: str,
) -> discord.Embed:
    """Create a RAXOR user profile embed."""

    return create_base_embed(
        title=f"✦ USER PROFILE // {title}",
        description=description,
        color=PROFILE_COLOR,
    )
