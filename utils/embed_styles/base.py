import discord

from utils.time import utc_now


# =========================
# RAXOR DESIGN SYSTEM
# =========================

RAXOR_PURPLE = 0x8B3DFF
RAXOR_GOLD = 0xD4AF37

RAXOR_FOOTER = "RAXOR • BUILT FOR A BETTER DISCORD EXPERIENCE"



# =========================
# Base Embed Builder
# =========================


def create_base_embed(
    *,
    title: str | None = None,
    description: str | None = None,
    color: discord.Color | None = None,
) -> discord.Embed:
    """Create a standardized RAXOR futuristic embed."""

    embed = discord.Embed(
        title=title,
        description=description,
        color=color or discord.color(RAXOR_PURPLE),
        timestamp=utc_now(),
    )

    embed.set_footer(
        text=RAXOR_FOOTER,
    )

    return embed
