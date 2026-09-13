import discord
from discord.ext import commands

from bot.checks import admin_only

from database.repositories import (
    get_leaderboard_reward_role,
    remove_leaderboard_reward_role,
    set_leaderboard_reward_role,
)

from utils.embeds import (
    error_embed,
    normal_embed,
    success_embed,
)


LEADERBOARD_TYPES = {
    "messages": "messages",
    "message": "messages",
    "voice": "voice",
}


class LeaderboardRewards(commands.Cog):
    """Weekly Top 3 leaderboard role reward configuration commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setleaderboardreward")
    @admin_only()
    @commands.guild_only()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def setleaderboardreward(
        self,
        ctx: commands.Context,
        leaderboard_type: str,
        role: discord.Role,
    ):
        """Set the role awarded to the weekly Top 3 for a leaderboard."""

        leaderboard_type = leaderboard_type.lower()

        if leaderboard_type not in LEADERBOARD_TYPES:
            await ctx.send(
                embed=error_embed(
                    title="Leaderboard Rewards",
                    description=(
                        "Invalid leaderboard type.\n\n"
                        "Usage: `₹setleaderboardreward "
                        "<messages|voice> @role`"
                    ),
                )
            )
            return

        if role >= ctx.guild.me.top_role:
            await ctx.send(
                embed=error_embed(
                    title="Leaderboard Rewards",
                    description=(
                        "I cannot assign that role because it is "
                        "equal to or higher than my own top role."
                    ),
                )
            )
            return

        db_type = LEADERBOARD_TYPES[leaderboard_type]

        await set_leaderboard_reward_role(
            self.bot.db_pool,
            ctx.guild.id,
            db_type,
            role.id,
        )

        await ctx.send(
            embed=success_embed(
                title="Leaderboard Reward Set",
                description=(
                    f"{role.mention} will now be awarded to the weekly "
                    f"**Top 3** in **{db_type}**."
                ),
            )
        )

    @commands.command(name="removeleaderboardreward")
    @admin_only()
    @commands.guild_only()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def removeleaderboardreward(
        self,
        ctx: commands.Context,
        leaderboard_type: str,
    ):
        """Remove the weekly Top 3 reward role for a leaderboard."""

        leaderboard_type = leaderboard_type.lower()

        if leaderboard_type not in LEADERBOARD_TYPES:
            await ctx.send(
                embed=error_embed(
                    title="Leaderboard Rewards",
                    description=(
                        "Invalid leaderboard type.\n\n"
                        "Usage: `₹removeleaderboardreward <messages|voice>`"
                    ),
                )
            )
            return

        db_type = LEADERBOARD_TYPES[leaderboard_type]

        await remove_leaderboard_reward_role(
            self.bot.db_pool,
            ctx.guild.id,
            db_type,
        )

        await ctx.send(
            embed=success_embed(
                title="Leaderboard Reward Removed",
                description=(
                    f"The weekly Top 3 reward role for **{db_type}** "
                    "has been removed."
                ),
            )
        )

    @commands.command(name="leaderboardrewards")
    @commands.guild_only()
    async def leaderboardrewards(self, ctx: commands.Context):
        """Show the configured weekly Top 3 leaderboard reward roles."""

        lines = []

        for db_type in ("messages", "voice"):
            role_id = await get_leaderboard_reward_role(
                self.bot.db_pool,
                ctx.guild.id,
                db_type,
            )

            if role_id is None:
                role_text = "Not configured"
            else:
                role = ctx.guild.get_role(role_id)
                role_text = role.mention if role else f"`{role_id}`"

            lines.append(f"**{db_type.title()}** — {role_text}")

        embed = normal_embed(
            title="Weekly Leaderboard Rewards",
            description="\n".join(lines),
        )

        await ctx.send(embed=embed)


async def setup(bot):
    """Load the leaderboard rewards command cog."""
    await bot.add_cog(LeaderboardRewards(bot))
