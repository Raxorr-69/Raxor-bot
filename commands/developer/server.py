import discord
from discord.ext import commands

from bot.checks import developer_only
from utils.embeds import developer_embed


# =========================
# Developer Server Commands
# =========================

@commands.hybird_command(name="servercount")
@developer_only()
async def server_count(ctx: commands.Context):
    """Show the total number of servers the bot is connected to."""

    bot = ctx.bot

    embed = developer_embed(
        "Server Count",
        "Global server information for the bot.",
    )

    embed.add_field(
        name="Connected Servers",
        value=f"`{len(bot.guilds)}`",
        inline=False,
    )

    await ctx.send(embed=embed)


@commands.hybird_command(name="serverlist")
@developer_only()
async def server_list(ctx: commands.Context):
    """Show a list of all servers the bot is connected to."""

    bot = ctx.bot

    embed = developer_embed(
        "Server List",
        "Servers currently connected to the bot.",
    )

    if not bot.guilds:
        embed.add_field(
            name="Servers",
            value="No servers found.",
            inline=False,
        )

        await ctx.send(embed=embed)
        return

    server_lines = []

    for guild in sorted(
        bot.guilds,
        key=lambda item: item.name.lower(),
    ):
        server_lines.append(
            f"• **{guild.name}**\n"
            f"  ID: `{guild.id}`"
        )

    description = "\n\n".join(server_lines)

    # Discord embed field/description limits require
    # large server lists to be split into multiple fields.
    chunks = []

    current_chunk = ""

    for line in server_lines:
        if len(current_chunk) + len(line) + 2 > 1000:
            chunks.append(current_chunk)
            current_chunk = line
        else:
            if current_chunk:
                current_chunk += "\n\n"

            current_chunk += line

    if current_chunk:
        chunks.append(current_chunk)

    # Keep the embed within Discord's field limit.
    for index, chunk in enumerate(chunks, start=1):
        embed.add_field(
            name=f"Servers {index}",
            value=chunk,
            inline=False,
        )

    await ctx.send(embed=embed)


@commands.hybird_command(name="serverlookup")
@developer_only()
async def server_info(
    ctx: commands.Context,
    server_id: int | None = None,
):
    """Show detailed information about a specific bot server."""

    if server_id is None:
        await ctx.send(
            embed=developer_embed(
                "Server Information",
                (
                    "Please provide a server ID.\n\n"
                    "Usage: `₹serverlookup <server_id>`"
                ),
            )
        )
        return

    bot = ctx.bot

    guild = bot.get_guild(server_id)

    if guild is None:
        await ctx.send(
            embed=developer_embed(
                "Server Information",
                (
                    f"No connected server was found "
                    f"with ID `{server_id}`."
                ),
            )
        )
        return

    members = guild.members

    bots = [
        member
        for member in members
        if member.bot
    ]

    humans = [
        member
        for member in members
        if not member.bot
    ]

    text_channels = [
        channel
        for channel in guild.channels
        if isinstance(
            channel,
            discord.TextChannel,
        )
    ]

    voice_channels = [
        channel
        for channel in guild.channels
        if isinstance(
            channel,
            discord.VoiceChannel,
        )
    ]

    categories = [
        channel
        for channel in guild.channels
        if isinstance(
            channel,
            discord.CategoryChannel,
        )
    ]

    owner = guild.owner

    embed = developer_embed(
        "Server Information",
        f"Global information for **{guild.name}**.",
    )

    if guild.icon:
        embed.set_thumbnail(
            url=guild.icon.url,
        )

    embed.add_field(
        name="Server",
        value=f"**{guild.name}**",
        inline=False,
    )

    embed.add_field(
        name="Server ID",
        value=f"`{guild.id}`",
        inline=True,
    )

    embed.add_field(
        name="Owner",
        value=(
            owner.mention
            if owner
            else f"`{guild.owner_id}`"
        ),
        inline=True,
    )

    embed.add_field(
        name="Members",
        value=f"`{guild.member_count}`",
        inline=True,
    )

    embed.add_field(
        name="Humans",
        value=f"`{len(humans)}`",
        inline=True,
    )

    embed.add_field(
        name="Bots",
        value=f"`{len(bots)}`",
        inline=True,
    )

    embed.add_field(
        name="Roles",
        value=f"`{len(guild.roles)}`",
        inline=True,
    )

    embed.add_field(
        name="Text Channels",
        value=f"`{len(text_channels)}`",
        inline=True,
    )

    embed.add_field(
        name="Voice Channels",
        value=f"`{len(voice_channels)}`",
        inline=True,
    )

    embed.add_field(
        name="Categories",
        value=f"`{len(categories)}`",
        inline=True,
    )

    embed.add_field(
        name="Verification",
        value=f"`{guild.verification_level.name}`",
        inline=True,
    )

    embed.add_field(
        name="Created",
        value=(
            f"<t:{int(guild.created_at.timestamp())}:F>"
        ),
        inline=False,
    )

    await ctx.send(embed=embed)


# =========================
# Extension Setup
# =========================

async def setup(bot):
    """Load developer server commands."""

    bot.add_command(server_count)
    bot.add_command(server_list)
    bot.add_command(server_info)
