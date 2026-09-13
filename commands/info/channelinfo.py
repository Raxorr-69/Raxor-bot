import discord
from discord.ext import commands

from database.repositories import get_channel_rules

from utils.embeds import normal_embed

class ChannelInfo(commands.Cog):
    """Channel information commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybird_command(name="channelinfo")
    @commands.guild_only()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def channelinfo(
        self,
        ctx,
        channel: discord.abc.GuildChannel = None,
    ):
        """Show information about a server channel."""

        channel = channel or ctx.channel

        embed = normal_embed(
            title="Channel Information",
            description=f"**{channel.name}**",
        )

        embed.add_field(
            name="Name",
            value=channel.name,
            inline=True,
        )

        embed.add_field(
            name="ID",
            value=str(channel.id),
            inline=True,
        )

        embed.add_field(
            name="Type",
            value=str(channel.type).replace("_", " ").title(),
            inline=True,
        )

        embed.add_field(
            name="Position",
            value=str(channel.position),
            inline=True,
        )

        category = getattr(channel, "category", None)

        embed.add_field(
            name="Category",
            value=category.mention if category else "No Category",
            inline=True,
        )

        created_at = discord.utils.format_dt(
            channel.created_at,
            style="F",
        )

        embed.add_field(
            name="Created",
            value=created_at,
            inline=False,
        )

        is_visible = channel.permissions_for(ctx.author).view_channel

        embed.add_field(
            name="Visibility",
            value="Public" if is_visible else "Private",
            inline=True,
        )

        rule = await get_channel_rules(
            self.bot.db_pool,
            ctx.guild.id,
            channel.id,
        )

        image_only = False
        clips_only = False

        if rule is not None:
            image_only = rule["image_only"]
            clips_only = rule["clips_only"]

        embed.add_field(
            name="Image Only",
            value="Enabled" if image_only else "Disabled",
            inline=True,
        )

        embed.add_field(
            name="Clips Only",
            value="Enabled" if clips_only else "Disabled",
            inline=True,
        )

        if isinstance(channel, discord.TextChannel):
            embed.add_field(
                name="Topic",
                value=channel.topic or "No topic",
                inline=False,
            )

            embed.add_field(
                name="Slowmode",
                value=f"{channel.slowmode_delay} seconds",
                inline=True,
            )

            embed.add_field(
                name="NSFW",
                value="Yes" if channel.nsfw else "No",
                inline=True,
            )

            embed.add_field(
                name="Threads",
                value=str(len(channel.threads)),
                inline=True,
            )

        elif isinstance(channel, discord.VoiceChannel):
            embed.add_field(
                name="Bitrate",
                value=f"{channel.bitrate // 1000} kbps",
                inline=True,
            )

            embed.add_field(
                name="User Limit",
                value=(
                    str(channel.user_limit)
                    if channel.user_limit
                    else "Unlimited"
                ),
                inline=True,
            )

            embed.add_field(
                name="Current Members",
                value=str(len(channel.members)),
                inline=True,
            )

            embed.add_field(
                name="RTC Region",
                value=str(channel.rtc_region or "Automatic"),
                inline=True,
            )

        overwrites = channel.overwrites

        embed.add_field(
            name="Permission Overwrites",
            value=str(len(overwrites)),
            inline=True,
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ChannelInfo(bot))
