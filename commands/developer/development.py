from discord.ext import commands

from bot.checks import developer_only
from utils.embeds import developer_embed


# =========================
# Developer Command List
# =========================

@commands.hybrid_command(name="devcommands")
@developer_only()
async def developer_commands(ctx: commands.Context):
    """Show the available developer commands."""

    embed = developer_embed(
        "Developer Commands",
        "Commands available to the bot developer.",
    )

    embed.add_field(
        name="Server",
        value=(
            "`₹servercount`\n"
            "`₹serverlist`\n"
            "`₹serverlookup <server_id>`"
        ),
        inline=False,
    )

    embed.add_field(
        name="Bot",
        value=(
            "`₹botinfo`\n"
            "`₹botstatus`"
        ),
        inline=False,
    )

    embed.add_field(
        name="Announcements",
        value=(
            "`₹announce <server_id> <content>`"
        ),
        inline=False,
    )

    embed.add_field(
        name="Development",
        value=(
            "`₹devcommands`"
        ),
        inline=False,
    )

    await ctx.send(embed=embed)


# =========================
# Extension Setup
# =========================

async def setup(bot):
    """Load developer development commands."""

    bot.add_command(developer_commands)
