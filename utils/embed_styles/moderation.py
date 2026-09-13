import discord

from utils.embed_styles.base import create_base_embed


# =========================
# Moderation Colors
# =========================

MODERATION_COLOR = discord.Color.dark_red()


# =========================
# Moderation Embed Builder
# =========================


def moderation_embed(
    title: str,
    description: str,
    fields: list[tuple[str, str, bool]] | None = None,
) -> discord.Embed:
    """Create a moderation embed."""

    embed = create_base_embed(
        title=f"🛡️ {title}",
        description=description,
        color=MODERATION_COLOR,
    )

    if fields:
        for name, value, inline in fields:
            embed.add_field(
                name=name,
                value=value,
                inline=inline,
            )

    return embed

