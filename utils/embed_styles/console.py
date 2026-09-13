import discord

from utils.embed_styles.base import create_base_embed


# =========================
# Console Colors
# =========================

CONSOLE_SUCCESS = discord.Color.green()
CONSOLE_ERROR = discord.Color.red()
CONSOLE_WARNING = discord.Color.gold()
CONSOLE_INFO = discord.Color.blue()
CONSOLE_DEVELOPER = discord.Color.purple()


# =========================
# Console Labels
# =========================

CONSOLE_SUCCESS_LABEL = "SYSTEM // SUCCESS"
CONSOLE_ERROR_LABEL = "SYSTEM // ERROR"
CONSOLE_WARNING_LABEL = "SYSTEM // WARNING"
CONSOLE_INFO_LABEL = "SYSTEM // INFO"
CONSOLE_DEVELOPER_LABEL = "SYSTEM // DEVELOPER"


# =========================
# Console Embed Builders
# =========================


def success_embed(
    title: str,
    description: str,
) -> discord.Embed:
    """Create a console-style success embed."""

    embed = create_base_embed(
        title=f"✓ {CONSOLE_SUCCESS_LABEL} | {title}",
        description=description,
        color=CONSOLE_SUCCESS,
    )

    embed.set_footer(
        text="STATUS: OPERATION COMPLETED",
    )

    return embed


def error_embed(
    title: str,
    description: str,
) -> discord.Embed:
    """Create a console-style error embed."""

    embed = create_base_embed(
        title=f"✕ {CONSOLE_ERROR_LABEL} | {title}",
        description=description,
        color=CONSOLE_ERROR,
    )

    embed.set_footer(
        text="STATUS: OPERATION FAILED",
    )

    return embed


def warning_embed(
    title: str,
    description: str,
) -> discord.Embed:
    """Create a console-style warning embed."""

    embed = create_base_embed(
        title=f"⚠ {CONSOLE_WARNING_LABEL} | {title}",
        description=description,
        color=CONSOLE_WARNING,
    )

    embed.set_footer(
        text="STATUS: ATTENTION REQUIRED",
    )

    return embed


def info_embed(
    title: str,
    description: str,
) -> discord.Embed:
    """Create a console-style information embed."""

    embed = create_base_embed(
        title=f"◆ {CONSOLE_INFO_LABEL} | {title}",
        description=description,
        color=CONSOLE_INFO,
    )

    embed.set_footer(
        text="STATUS: INFORMATION",
    )

    return embed


def developer_embed(
    title: str,
    description: str,
) -> discord.Embed:
    """Create a console-style developer embed."""

    embed = create_base_embed(
        title=f"⌘ {CONSOLE_DEVELOPER_LABEL} | {title}",
        description=description,
        color=CONSOLE_DEVELOPER,
    )

    embed.set_footer(
        text="STATUS: DEVELOPER SYSTEM",
    )

    return embed


