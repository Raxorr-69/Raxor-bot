import discord
from discord.ext import commands

from utils.embeds import normal_embed

class Avatar(commands.Cog):
    """Member avatar commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="avatar")
    @commands.guild_only()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def avatar(self, ctx, member: discord.Member = None):
        """Show a member's avatar."""

        member = member or ctx.author

        avatar_url = member.display_avatar.url

        embed = normal_embed(
            title="Avatar",
            description=f"**{member.display_name}**",
        )

        embed.set_image(url=avatar_url)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Avatar(bot))

