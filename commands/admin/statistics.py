import discord
from discord.ext import commands

from bot.checks import admin_only
from database.repositories import (
    add_statistics_excluded_channel,
    get_statistics_excluded_channels,
    remove_statistics_excluded_channel,
)
from utils.embeds import normal_embed


class Statistics(commands.Cog):
    """Statistics configuration commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybird_command(name="statsblacklist")
    @admin_only()
    @commands.guild_only()
    async def statsblacklist(self, ctx, channel: discord.TextChannel = None):
        """Toggle a channel in the statistics exclusion list."""

        channel = channel or ctx.channel

        excluded_channels = await get_statistics_excluded_channels(
            self.bot.db_pool,
            ctx.guild.id,
        )

        excluded_channel_ids = {
            row["channel_id"]
            for row in excluded_channels
        }

        if channel.id in excluded_channel_ids:
            await remove_statistics_excluded_channel(
                self.bot.db_pool,
                ctx.guild.id,
                channel.id,
            )

            await ctx.send(
                embed=normal_embed(
                    title="Statistics Blacklist",
                    description=(
                        f"Statistics blacklist removed from "
                        f"{channel.mention}."
                    ),
                )
            )
            return

        await add_statistics_excluded_channel(
            self.bot.db_pool,
            ctx.guild.id,
            channel.id,
        )

        await ctx.send(
            embed=normal_embed(
                title="Statistics Blacklist",
                description=(
                    f"{channel.mention} has been added to "
                    f"the statistics blacklist."
                ),
            )
        )


async def setup(bot):
    await bot.add_cog(Statistics(bot))
