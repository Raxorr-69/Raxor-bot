import discord
from discord.ext import commands

from database.repositories import get_user

from utils.embeds import error_embed, profile_embed

class Profile(commands.Cog):
    """Member profile commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="profile")
    @commands.guild_only()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def profile(self, ctx):
        """Show the user's profile."""

        user = await get_user(
            self.bot.db_pool,
            ctx.author.id,
            ctx.guild.id,
        )

        if user is None:
            await ctx.send(
                embed=error_embed(
                    title="Profile",
                    description="Your profile has not been created yet.",
                )
            )
            return

        username = ctx.author.display_name
        level = user["level"]
        xp = user["xp"]
        message_count = user["message_count"]

        embed = profile_embed(
            title="Profile",
            description=f"**{username}**",
        )

        embed.add_field(
            name="Level",
            value=str(level),
            inline=True,
        )

        embed.add_field(
            name="XP",
            value=str(xp),
            inline=True,
        )

        embed.add_field(
            name="Messages",
            value=str(message_count),
            inline=True,
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Profile(bot))
