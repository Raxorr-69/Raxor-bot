import discord
from discord.ext import commands

from bot.checks import admin_only
from database.repositories import (
    create_channel_rules,
    get_channel_rules,
    update_channel_rule,
)
from utils.embed_styles.console import (
    error_embed,
    success_embed,
)


class Restrictions(commands.Cog):
    """Channel restriction configuration commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="imageonly")
    @admin_only()
    @commands.guild_only()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def imageonly(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel = None,
        value: str = "on",
    ):
        """Enable or disable image-only mode for a channel."""

        channel = channel or ctx.channel
        value = value.lower()

        if value not in {"on", "off"}:
            await ctx.send(
                embed=error_embed(
                    title="Channel Restriction",
                    description="Invalid value. Use `on` or `off`.",
                )
            )
            return

        rule = await get_channel_rules(
            self.bot.db_pool,
            ctx.guild.id,
            channel.id,
        )

        if rule is None:
            await create_channel_rules(
                self.bot.db_pool,
                ctx.guild.id,
                channel.id,
            )

        await update_channel_rule(
            self.bot.db_pool,
            ctx.guild.id,
            channel.id,
            "image_only",
            value == "on",
        )

        status = "enabled" if value == "on" else "disabled"

        await ctx.send(
            embed=success_embed(
                title="Channel Restriction",
                description=(
                    f"Image-only mode has been {status} "
                    f"for {channel.mention}."
                ),
            )
        )

    @commands.command(name="clipsonly")
    @admin_only()
    @commands.guild_only()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def clipsonly(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel = None,
        value: str = "on",
    ):
        """Enable or disable clips-only mode for a channel."""

        channel = channel or ctx.channel
        value = value.lower()

        if value not in {"on", "off"}:
            await ctx.send(
                embed=error_embed(
                    title="Channel Restriction",
                    description="Invalid value. Use `on` or `off`.",
                )
            )
            return

        rule = await get_channel_rules(
            self.bot.db_pool,
            ctx.guild.id,
            channel.id,
        )

        if rule is None:
            await create_channel_rules(
                self.bot.db_pool,
                ctx.guild.id,
                channel.id,
            )

        await update_channel_rule(
            self.bot.db_pool,
            ctx.guild.id,
            channel.id,
            "clips_only",
            value == "on",
        )

        status = "enabled" if value == "on" else "disabled"

        await ctx.send(
            embed=success_embed(
                title="Channel Restriction",
                description=(
                    f"Clips-only mode has been {status} "
                    f"for {channel.mention}."
                ),
            )
        )


async def setup(bot):
    """Load the restrictions command cog."""
    await bot.add_cog(Restrictions(bot))

