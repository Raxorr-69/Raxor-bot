import discord
from discord.ext import commands

from bot.checks import server_owner_only
from database.repositories import (
    add_whitelist,
    remove_whitelist,
)
from utils.embed_styles.console import (
    error_embed,
    success_embed,
)


class Whitelist(commands.Cog):
    """Server owner whitelist commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybird_command(name="whitelist")
    @server_owner_only()
    @commands.guild_only()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def whitelist(
        self,
        ctx: commands.Context,
        restriction: str,
        target: discord.Member | discord.Role,
    ):
        """Whitelist a user or role from a channel restriction."""

        restriction_map = {
            "image": "image_only",
            "images": "image_only",
            "clip": "clips_only",
            "clips": "clips_only",
        }

        restriction = restriction.lower()

        if restriction not in restriction_map:
            await ctx.send(
                embed=error_embed(
                    title="Whitelist",
                    description="Invalid restriction. Use `image` or `clips`.",
                )
            )
            return

        restriction_type = restriction_map[restriction]

        await add_whitelist(
            self.bot.db_pool,
            ctx.guild.id,
            target.id,
            restriction_type,
        )

        target_name = target.mention

        await ctx.send(
            embed=success_embed(
                title="Whitelist Updated",
                description=(
                    f"{target_name} has been whitelisted for "
                    f"`{restriction}` restrictions."
                ),
            )
        )

    @commands.hybird_command(name="unwhitelist")
    @server_owner_only()
    @commands.guild_only()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def unwhitelist(
        self,
        ctx: commands.Context,
        restriction: str,
        target: discord.Member | discord.Role,
    ):
        """Remove a user or role from a channel restriction whitelist."""

        restriction_map = {
            "image": "image_only",
            "images": "image_only",
            "clip": "clips_only",
            "clips": "clips_only",
        }

        restriction = restriction.lower()

        if restriction not in restriction_map:
            await ctx.send(
                embed=error_embed(
                    title="Whitelist",
                    description="Invalid restriction. Use `image` or `clips`.",
                )
            )
            return

        restriction_type = restriction_map[restriction]

        await remove_whitelist(
            self.bot.db_pool,
            ctx.guild.id,
            target.id,
            restriction_type,
        )

        target_name = target.mention

        await ctx.send(
            embed=success_embed(
                title="Whitelist Updated",
                description=(
                    f"{target_name} has been removed from the "
                    f"`{restriction}` whitelist."
                ),
            )
        )


async def setup(bot):
    await bot.add_cog(Whitelist(bot))


