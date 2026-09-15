import discord
from discord.ext import commands

from bot.checks import admin_only
from database.repositories import (
    create_guild,
    get_guild,
    update_guild_setting,
)
from utils.embeds import (
    error_embed,
    info_embed,
    success_embed,
)


# =========================
# Configuration Command
# =========================

@commands.hybrid_command(name="config")
@admin_only()
@commands.cooldown(5, 10, commands.BucketType.user)
async def config_command(
    ctx: commands.Context,
    category: str | None = None,
    setting: str | None = None,
    value: str | None = None,
):
    """View or update server configuration."""

    if ctx.guild is None:
        await ctx.send(
            embed=error_embed(
                "Configuration",
                "This command can only be used inside a server.",
            )
        )
        return

    pool = ctx.bot.db_pool

    guild = await get_guild(
        pool,
        ctx.guild.id,
    )

    if guild is None:
        await create_guild(
            pool,
            ctx.guild.id,
        )

        guild = await get_guild(
            pool,
            ctx.guild.id,
        )

    # =========================
    # Show Configuration
    # =========================

    if category is None:
        embed = info_embed(
            "Server Configuration",
            "Current configuration for this server.",
        )

        embed.add_field(
            name="Message Tracking",
            value=(
                "Enabled"
                if guild["message_tracking_enabled"]
                else "Disabled"
            ),
            inline=True,
        )

        embed.add_field(
            name="Voice Tracking",
            value=(
                "Enabled"
                if guild["voice_tracking_enabled"]
                else "Disabled"
            ),
            inline=True,
        )

        embed.add_field(
            name="Leveling",
            value=(
                "Enabled"
                if guild["leveling_enabled"]
                else "Disabled"
            ),
            inline=True,
        )

        embed.add_field(
            name="XP Range",
            value=(
                f"`{guild['xp_min']}` - "
                f"`{guild['xp_max']}` XP"
            ),
            inline=True,
        )

        embed.add_field(
            name="Level-Up Messages",
            value=(
                "Enabled"
                if guild["level_up_messages_enabled"]
                else "Disabled"
            ),
            inline=True,
        )

        level_up_channel_id = guild["level_up_channel_id"]

        if level_up_channel_id:
            channel = ctx.guild.get_channel(
                level_up_channel_id
            )

            level_up_channel = (
                channel.mention
                if channel
                else "Channel not found"
            )
        else:
            level_up_channel = "Not configured"

        embed.add_field(
            name="Level-Up Channel",
            value=level_up_channel,
            inline=True,
        )

        await ctx.send(embed=embed)
        return

    # =========================
    # Boolean Settings
    # =========================

    boolean_settings = {
        "messages": "message_tracking_enabled",
        "message": "message_tracking_enabled",
        "voice": "voice_tracking_enabled",
        "leveling": "leveling_enabled",
        "levelup": "level_up_messages_enabled",
    }

    category = category.lower()

    if category in boolean_settings:
        if setting is None:
            await ctx.send(
                embed=error_embed(
                    "Configuration",
                    f"Usage: `₹config {category} "
                    f"on/off`",
                )
            )
            return

        if setting.lower() not in {"on", "off"}:
            await ctx.send(
                embed=error_embed(
                    "Configuration",
                    "Value must be `on` or `off`.",
                )
            )
            return

        enabled = setting.lower() == "on"
        database_setting = boolean_settings[category]

        try:
            await update_guild_setting(
                pool,
                ctx.guild.id,
                database_setting,
                enabled,
            )
        except ValueError as exc:
            await ctx.send(
                embed=error_embed(
                    "Configuration",
                    str(exc),
                )
            )
            return

        status = "enabled" if enabled else "disabled"

        await ctx.send(
            embed=success_embed(
                "Configuration Updated",
                f"**{category.title()}** has been "
                f"**{status}**.",
            )
        )
        return

    # =========================
    # XP Configuration
    # =========================

    if category == "xp":
        if setting is None or value is None:
            await ctx.send(
                embed=error_embed(
                    "Configuration",
                    "Usage: `₹config xp <min> <max>`",
                )
            )
            return

        try:
            xp_min = int(setting)
            xp_max = int(value)
        except ValueError:
            await ctx.send(
                embed=error_embed(
                    "Configuration",
                    "XP minimum and maximum must "
                    "both be integers.",
                )
            )
            return

        if xp_min < 1 or xp_max < 1:
            await ctx.send(
                embed=error_embed(
                    "Configuration",
                    "XP values must be greater than zero.",
                )
            )
            return

        if xp_min > xp_max:
            await ctx.send(
                embed=error_embed(
                    "Configuration",
                    "Minimum XP cannot be greater "
                    "than maximum XP.",
                )
            )
            return

        try:
            await update_guild_setting(
                pool,
                ctx.guild.id,
                "xp_min",
                xp_min,
            )

            await update_guild_setting(
                pool,
                ctx.guild.id,
                "xp_max",
                xp_max,
            )
        except ValueError as exc:
            await ctx.send(
                embed=error_embed(
                    "Configuration",
                    str(exc),
                )
            )
            return

        await ctx.send(
            embed=success_embed(
                "XP Configuration Updated",
                (
                    f"XP range has been set to "
                    f"**{xp_min} - {xp_max} XP**."
                ),
            )
        )
        return

    # =========================
    # Level-Up Channel
    # =========================

    if category in {"levelupchannel", "levelup-channel"}:
        if setting is None:
            await ctx.send(
                embed=error_embed(
                    "Configuration",
                    "Mention a text channel.",
                )
            )
            return

        channel_id = None

        if ctx.message.channel_mentions:
            channel = ctx.message.channel_mentions[0]

            if not isinstance(
                channel,
                discord.TextChannel,
            ):
                await ctx.send(
                    embed=error_embed(
                        "Configuration",
                        "Level-up channel must be "
                        "a text channel.",
                    )
                )
                return

            channel_id = channel.id

        else:
            await ctx.send(
                embed=error_embed(
                    "Configuration",
                    "Please mention a text channel, "
                    "for example `#level-up`.",
                )
            )
            return

        try:
            await update_guild_setting(
                pool,
                ctx.guild.id,
                "level_up_channel_id",
                channel_id,
            )
        except ValueError as exc:
            await ctx.send(
                embed=error_embed(
                    "Configuration",
                    str(exc),
                )
            )
            return

        await ctx.send(
            embed=success_embed(
                "Level-Up Channel Updated",
                (
                    f"Level-up messages will now be "
                    f"sent in {channel.mention}."
                ),
            )
        )
        return



    # =========================
    # Announcement Channel
    # =========================

    if category in {
        "announcementchannel",
        "announcement-channel",
        "announcechannel",
    }:
        if setting is None:
            await ctx.send(
                embed=error_embed(
                    "Configuration",
                    "Mention a text channel.",
                )
            )
            return

        if not ctx.message.channel_mentions:
            await ctx.send(
                embed=error_embed(
                    "Configuration",
                    (
                        "Please mention a text channel, "
                        "for example `#announcements`."
                    ),
                )
            )
            return

        channel = ctx.message.channel_mentions[0]

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            await ctx.send(
                embed=error_embed(
                    "Configuration",
                    "Announcement channel must be a text channel.",
                )
            )
            return

        try:
            await update_guild_setting(
                pool,
                ctx.guild.id,
                "announcement_channel_id",
                channel.id,
            )
        except ValueError as exc:
            await ctx.send(
                embed=error_embed(
                    "Configuration",
                    str(exc),
                )
            )
            return

        await ctx.send(
            embed=success_embed(
                "Announcement Channel Updated",
                (
                    f"Developer announcements will now be "
                    f"sent in {channel.mention}."
                ),
            )
        )
        return




    # =========================
    # Invalid Category
    # =========================

    await ctx.send(
        embed=error_embed(
            "Configuration",
            (
                f"Unknown configuration category "
                f"`{category}`.\n\n"
                "Available categories:\n"
                "• `messages`\n"
                "• `voice`\n"
                "• `leveling`\n"
                "• `levelup`\n"
                "• `xp`\n"
                "• `levelupchannel`"
            ),
        )
    )


# =========================
# Extension Setup
# =========================

async def setup(bot):
    """Load the configuration command."""
    bot.add_command(config_command)
