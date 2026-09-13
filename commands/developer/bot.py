import discord
from discord.ext import commands

from bot.checks import developer_only
from utils.embeds import developer_embed


# =========================
# Developer Bot Commands
# =========================

@commands.hybird_command(name="botinfo")
@developer_only()
async def bot_info(ctx: commands.Context):
    """Show detailed information about the bot."""

    bot = ctx.bot
    user = bot.user

    if user is None:
        await ctx.send(
            embed=developer_embed(
                "Bot Information",
                "Bot information is currently unavailable.",
            )
        )
        return

    embed = developer_embed(
        "Bot Information",
        "Global information about the bot.",
    )

    if user.avatar:
        embed.set_thumbnail(
            url=user.avatar.url,
        )

    embed.add_field(
        name="Bot",
        value=f"**{user.name}**",
        inline=False,
    )

    embed.add_field(
        name="Bot ID",
        value=f"`{user.id}`",
        inline=True,
    )

    embed.add_field(
        name="Servers",
        value=f"`{len(bot.guilds)}`",
        inline=True,
    )

    embed.add_field(
        name="Users",
        value=f"`{len(bot.users)}`",
        inline=True,
    )

    embed.add_field(
        name="Latency",
        value=f"`{round(bot.latency * 1000)} ms`",
        inline=True,
    )

    embed.add_field(
        name="Discord.py",
        value=f"`{discord.__version__}`",
        inline=True,
    )

    embed.add_field(
        name="Command Prefix",
        value="`₹`",
        inline=True,
    )

    embed.add_field(
        name="Bot Account Created",
        value=discord.utils.format_dt(
            user.created_at,
            style="F",
        ),
        inline=True,
    )

    await ctx.send(embed=embed)


@commands.command(name="botstatus")
@developer_only()
async def bot_status(ctx: commands.Context):
    """Show the current bot runtime status."""

    bot = ctx.bot

    latency = round(bot.latency * 1000)

    if latency < 150:
        connection_status = "Excellent"
    elif latency < 300:
        connection_status = "Stable"
    elif latency < 500:
        connection_status = "Slow"
    else:
        connection_status = "High Latency"

    embed = developer_embed(
        "Bot Status",
        "Current runtime status of the bot.",
    )

    embed.add_field(
        name="Connection",
        value="`Online`",
        inline=True,
    )

    embed.add_field(
        name="Latency",
        value=f"`{latency} ms`",
        inline=True,
    )

    embed.add_field(
        name="Connection Quality",
        value=f"`{connection_status}`",
        inline=True,
    )

    embed.add_field(
        name="Connected Servers",
        value=f"`{len(bot.guilds)}`",
        inline=True,
    )

    embed.add_field(
        name="Cached Users",
        value=f"`{len(bot.users)}`",
        inline=True,
    )

    await ctx.send(embed=embed)


# =========================
# Extension Setup
# =========================

async def setup(bot):
    """Load developer bot commands."""

    bot.add_command(bot_info)
    bot.add_command(bot_status)
