import discord

from utils.embed_styles.base import create_base_embed


# =========================
# Normal Embed Color
# =========================

NORMAL_COLOR = discord.Color.blurple()


# =========================
# Normal Embed Builder
# =========================


def normal_embed(
    title: str,
    description: str,
) -> discord.Embed:
    """Create a clean normal bot-message embed."""

    return create_base_embed(
        title=title,
        description=description,
        color=NORMAL_COLOR,
    )
