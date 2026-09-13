import discord
from discord.ext import commands

from bot.checks import developer_only
from database.repositories import get_guild
from utils.embeds import developer_embed


# =========================
# Developer Announcement
# =========================

@commands.hybird_command(name="announce")
@developer_only()
async def announce(
    ctx: commands.Context,
    server_id: int | None = None,
    *,
    content: str | None = None,
):
    """Send a developer announcement to a configured server channel."""

    if server_id is None or not content:
        await ctx.send(
            embed=developer_embed(
                "Announcement",
                (
                    "Missing announcement details.\n\n"
                    "Usage:\n"
                    "`₹announce <server_id> <content>`"
                ),
            )
        )
        return

    bot = ctx.bot
    pool = bot.db_pool

    # =========================
    # Find Server
    # =========================

    guild = bot.get_guild(server_id)

    if guild is None:
        await ctx.send(
            embed=developer_embed(
                "Announcement Failed",
                (
                    f"No connected server was found "
                    f"with ID `{server_id}`."
                ),
            )
        )
        return

    # =========================
    # Get Server Configuration
    # =========================

    guild_data = await get_guild(
        pool,
        guild.id,
    )

    if guild_data is None:
        await ctx.send(
            embed=developer_embed(
                "Announcement Failed",
                (
                    f"No configuration record exists "
                    f"for **{guild.name}**."
                ),
            )
        )
        return

    channel_id = guild_data[
        "announcement_channel_id"
    ]

    if channel_id is None:
        await ctx.send(
            embed=developer_embed(
                "Announcement Failed",
                (
                    f"No announcement channel has been "
                    f"configured for **{guild.name}**.\n\n"
                    "Configure one with:\n"
                    "`₹config announcementchannel #channel`"
                ),
            )
        )
        return

    # =========================
    # Find Announcement Channel
    # =========================

    channel = guild.get_channel(channel_id)

    if channel is None:
        await ctx.send(
            embed=developer_embed(
                "Announcement Failed",
                (
                    "The configured announcement channel "
                    "could not be found.\n\n"
                    "The channel may have been deleted."
                ),
            )
        )
        return

    if not isinstance(
        channel,
        discord.TextChannel,
    ):
        await ctx.send(
            embed=developer_embed(
                "Announcement Failed",
                "The configured announcement channel is not a text channel.",
            )
        )
        return

    # =========================
    # Build Announcement
    # =========================

    announcement_embed = developer_embed(
        "Developer Announcement",
        content,
    )

    announcement_embed.set_footer(
        text="Raxor // Developer Announcement",
    )

    # =========================
    # Send Announcement
    # =========================

    try:
        await channel.send(
            embed=announcement_embed,
        )

    except discord.Forbidden:
        await ctx.send(
            embed=developer_embed(
                "Announcement Failed",
                (
                    f"I don't have permission to send "
                    f"messages in {channel.mention}."
                ),
            )
        )
        return

    except discord.HTTPException:
        await ctx.send(
            embed=developer_embed(
                "Announcement Failed",
                (
                    f"Discord rejected the announcement "
                    f"request for **{guild.name}**."
                ),
            )
        )
        return

    # =========================
    # Confirmation
    # =========================

    await ctx.send(
        embed=developer_embed(
            "Announcement Sent",
            (
                f"Announcement successfully sent to "
                f"**{guild.name}**.\n\n"
                f"Channel: {channel.mention}\n"
                f"Server ID: `{guild.id}`"
            ),
        )
    )


# =========================
# Extension Setup
# =========================

async def setup(bot):
    """Load developer announcement commands."""

    bot.add_command(announce)
