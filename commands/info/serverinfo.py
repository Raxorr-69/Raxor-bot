import discord
from discord.ext import commands

from utils.embeds import normal_embed
from utils.formatters import truncate_field

class ServerInfo(commands.Cog):
    """Server information commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="serverinfo")
    @commands.guild_only()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def serverinfo(self, ctx):
        """Show information about the current server."""

        guild = ctx.guild

        members = guild.members
        bots = [member for member in members if member.bot]

        text_channels = [
            channel
            for channel in guild.channels
            if isinstance(channel, discord.TextChannel)
        ]

        voice_channels = [
            channel
            for channel in guild.channels
            if isinstance(channel, discord.VoiceChannel)
        ]

        visible_channels = [
            channel
            for channel in guild.channels
            if channel.permissions_for(ctx.author).view_channel
        ]

        private_channels = [
            channel
            for channel in guild.channels
            if not channel.permissions_for(ctx.author).view_channel
        ]

        admins = [
            member
            for member in members
            if member.guild_permissions.administrator
        ]

        owner = guild.owner

        embed = normal_embed(
            title="Server Information",
            description=f"**{guild.name}**",
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(
            name="Server ID",
            value=str(guild.id),
            inline=True,
        )

        embed.add_field(
            name="Owner",
            value=owner.mention if owner else "Unknown",
            inline=True,
        )

        embed.add_field(
            name="Members",
            value=str(guild.member_count),
            inline=True,
        )

        embed.add_field(
            name="Bots",
            value=str(len(bots)),
            inline=True,
        )

        embed.add_field(
            name="Roles",
            value=str(len(guild.roles)),
            inline=True,
        )

        embed.add_field(
            name="Text Channels",
            value=str(len(text_channels)),
            inline=True,
        )

        embed.add_field(
            name="Voice Channels",
            value=str(len(voice_channels)),
            inline=True,
        )

        embed.add_field(
            name="Visible Channels",
            value=str(len(visible_channels)),
            inline=True,
        )

        embed.add_field(
            name="Locked Channels",
            value=str(len(private_channels)),
            inline=True,
        )

        admin_text = ", ".join(
            member.mention
            for member in admins
        )

        if not admin_text:
            admin_text = "No administrators found"
        else:
            admin_text = truncate_field(admin_text)

        embed.add_field(
            name="Administrators",
            value=admin_text,
            inline=False,
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ServerInfo(bot))
