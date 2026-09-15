from discord.ext import commands

from database.repositories import set_afk

from utils.embeds import normal_embed

# Cap stored AFK reasons so they can never overflow a Discord embed
# field (1024 chars) or, combined across several mentioned AFK users
# in one message, an embed description (4096 chars).
MAX_AFK_REASON_LENGTH = 200


class AFK(commands.Cog):
    """AFK status commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="afk")
    @commands.guild_only()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def afk(self, ctx, *, reason: str = "AFK"):
        """Set the user's AFK status."""

        reason = reason.strip() or "AFK"

        if len(reason) > MAX_AFK_REASON_LENGTH:
            reason = reason[: MAX_AFK_REASON_LENGTH - 1].rstrip() + "…"

        await set_afk(
            self.bot.db_pool,
            ctx.guild.id,
            ctx.author.id,
            reason,
        )

        embed = normal_embed(
            title="AFK",
            description=f"{ctx.author.mention} is now AFK.",
        )

        embed.add_field(
            name="Reason",
            value=f"`{reason}`",
            inline=False,
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AFK(bot))
