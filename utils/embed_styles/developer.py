import discord

from utils.embed_styles.base import create_base_embed


# =========================
# Developer Colors
# =========================

DEVELOPER_COLOR = discord.Color.purple()


# =========================
# Developer Embed Builder
# =========================


def developer_embed(
    title: str,
    description: str,
) -> discord.Embed:
    """Create a developer-system embed."""

    return create_base_embed(
        title=f"⌘ DEVELOPER // {title}",
        description=description,
        color=DEVELOPER_COLOR,
    )
