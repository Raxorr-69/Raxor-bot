import discord

from utils.embed_styles.base import create_base_embed


# =========================
# Leaderboard Colors
# =========================

LEADERBOARD_COLOR = discord.Color(0xD4AF37)

LEADERBOARD_GOLD = 0xD4AF37

# =========================
# Leaderboard Embed Builder
# =========================


def leaderboard_embed(
    title: str,
    description: str | None = None,
    *,
    footer: str | None = None,
) -> discord.Embed:
    """Create a RAXOR futuristic gold leaderboard embed."""

    embed = create_base_embed(
        title=f"◈ LEADERBOARD 🏆 {title}",
        description=description,
        color=LEADERBOARD_COLOR,
    )

    if footer is not None:
        embed.set_footer(text=footer)

    return embed


# =========================
# Leaderboard Entry Formatter
# =========================


def leaderboard_entry(
    position: int,
    name: str,
    value: str,
) -> str:
    """Format one leaderboard entry."""

    medals = {
        1: "🥇",
        2: "🥈",
        3: "🥉",
    }

    prefix = medals.get(
        position,
        f"`#{position}`",
    )

    return f"{prefix} **{name}** — `{value}`"



# =========================
# Leaderboard With Entries
# =========================


def leaderboard_embed_with_entries(
    title: str,
    entries: list[str],
    *,
    description: str | None = None,
    footer: str | None = None,
) -> discord.Embed:
    """Create a RAXOR leaderboard embed with formatted entries."""

    embed = leaderboard_embed(
        title,
        description,
        footer=footer,
    )

    if entries:
        embed.add_field(
            name="RANKINGS",
            value="\n".join(entries),
            inline=False,
        )

    return embed
