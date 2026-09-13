import discord
from discord.ext import commands

from database.repositories import get_inviter, get_user

from utils.embeds import normal_embed
from utils.formatters import truncate_field

class UserInfo(commands.Cog):
    """User information commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="userinfo")
    @commands.guild_only()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def userinfo(
        self,
        ctx,
        member: discord.Member = None,
    ):
        """Show information about a server member."""

        member = member or ctx.author

        user_data = await get_user(
            self.bot.db_pool,
            member.id,
            ctx.guild.id,
        )

        if user_data is None:
            warnings = 0
        else:
            warnings = user_data["warnings"]

        inviter_id = await get_inviter(
            self.bot.db_pool,
            ctx.guild.id,
            member.id,
        )

        inviter = None

        if inviter_id is not None:
            inviter = ctx.guild.get_member(inviter_id)

        roles = [
            role.mention
            for role in member.roles
            if role != ctx.guild.default_role
        ]

        highest_role = member.top_role

        permissions = [
            permission.replace("_", " ").title()
            for permission, enabled in highest_role.permissions
            if enabled
        ]

        if not permissions:
            permissions_text = "No special permissions"
        else:
            permissions_text = truncate_field(", ".join(permissions))

        roles_text = truncate_field(", ".join(roles)) if roles else "No roles"

        if inviter is not None:
            inviter_text = inviter.mention
        elif inviter_id is not None:
            inviter_text = f"<@{inviter_id}>"
        else:
            inviter_text = "Unknown"

        join_date = (
            discord.utils.format_dt(member.joined_at, style="F")
            if member.joined_at
            else "Unknown"
        )

        account_created = discord.utils.format_dt(
            member.created_at,
            style="F",
        )

        embed = normal_embed(
            title="User Information",
            description=f"**{member.display_name}**",
        )

        embed.set_thumbnail(
            url=member.display_avatar.url
        )

        embed.add_field(
            name="Username",
            value=str(member),
            inline=True,
        )

        embed.add_field(
            name="Display Name",
            value=member.display_name,
            inline=True,
        )

        embed.add_field(
            name="User ID",
            value=str(member.id),
            inline=True,
        )

        embed.add_field(
            name="Account Created",
            value=account_created,
            inline=False,
        )

        embed.add_field(
            name="Joined Server",
            value=join_date,
            inline=False,
        )

        embed.add_field(
            name="Roles",
            value=roles_text,
            inline=False,
        )

        embed.add_field(
            name="Highest Role",
            value=highest_role.mention,
            inline=True,
        )

        embed.add_field(
            name="Highest Role Permissions",
            value=permissions_text,
            inline=False,
        )

        embed.add_field(
            name="Warnings",
            value=str(warnings),
            inline=True,
        )

        embed.add_field(
            name="Invited By",
            value=inviter_text,
            inline=True,
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(UserInfo(bot))
