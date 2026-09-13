import discord
from discord.ext import commands

from bot.checks import admin_only

from services.leveling import (
    add_level_reward,
    remove_level_reward,
)

from database.repositories import get_all_level_rewards

from utils.embeds import (
    error_embed,
    normal_embed,
    success_embed,
)


class LevelRewards(commands.Cog):
    """Level-up role reward configuration commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="addlevelreward")
    @admin_only()
    @commands.guild_only()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def addlevelreward(
        self,
        ctx: commands.Context,
        level: int,
        role: discord.Role,
    ):
        """Add a role reward for reaching a level."""

        if level < 1:
            await ctx.send(
                embed=error_embed(
                    title="Level Rewards",
                    description="Level must be greater than or equal to 1.",
                )
            )
            return

        if role >= ctx.guild.me.top_role:
            await ctx.send(
                embed=error_embed(
                    title="Level Rewards",
                    description=(
                        "I cannot assign that role because it is "
                        "equal to or higher than my own top role."
                    ),
                )
            )
            return

        try:
            await add_level_reward(
                self.bot.db_pool,
                ctx.guild.id,
                level,
                role.id,
            )
        except ValueError as exc:
            await ctx.send(
                embed=error_embed(
                    title="Level Rewards",
                    description=str(exc),
                )
            )
            return

        await ctx.send(
            embed=success_embed(
                title="Level Reward Added",
                description=(
                    f"{role.mention} will now be awarded at "
                    f"**Level {level}**."
                ),
            )
        )

    @commands.command(name="removelevelreward")
    @admin_only()
    @commands.guild_only()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def removelevelreward(
        self,
        ctx: commands.Context,
        level: int,
        role: discord.Role,
    ):
        """Remove a role reward from a level."""

        await remove_level_reward(
            self.bot.db_pool,
            ctx.guild.id,
            level,
            role.id,
        )

        await ctx.send(
            embed=success_embed(
                title="Level Reward Removed",
                description=(
                    f"{role.mention} will no longer be awarded at "
                    f"**Level {level}**."
                ),
            )
        )

    @commands.command(name="levelrewards")
    @commands.guild_only()
    async def levelrewards(self, ctx: commands.Context):
        """List all configured level-up role rewards."""

        rewards = await get_all_level_rewards(
            self.bot.db_pool,
            ctx.guild.id,
        )

        if not rewards:
            await ctx.send(
                embed=normal_embed(
                    title="Level Rewards",
                    description="No level rewards have been configured yet.",
                )
            )
            return

        lines = []

        for reward in rewards:
            role = ctx.guild.get_role(reward["role_id"])
            role_text = role.mention if role else f"`{reward['role_id']}`"

            lines.append(
                f"**Level {reward['level']}** — {role_text}"
            )

        embed = normal_embed(
            title="Level Rewards",
            description="\n".join(lines),
        )

        await ctx.send(embed=embed)


async def setup(bot):
    """Load the level rewards command cog."""
    await bot.add_cog(LevelRewards(bot))
