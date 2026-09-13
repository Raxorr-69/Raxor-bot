import discord
from discord import app_commands
from discord.ext import commands

from services import leaderboard as leaderboard_service

from utils.embeds import (
    error_embed,
    leaderboard_embed,
)

from utils.formatters import format_duration, format_number


class Leaderboard(commands.Cog):
    """Leaderboard commands."""

    def __init__(self, bot):
        self.bot = bot

    async def _get_results(
        self,
        guild_id: int,
        category: str,
        period: str | None,
    ):
        """Fetch leaderboard results."""

        if category == "level":
            return await leaderboard_service.get_level_leaderboard(
                self.bot.db_pool,
                guild_id,
            )

        if period == "all":
            if category == "messages":
                return await leaderboard_service.get_all_message_leaderboard(
                    self.bot.db_pool,
                    guild_id,
                )

            if category == "voice":
                return await leaderboard_service.get_all_voice_leaderboard(
                    self.bot.db_pool,
                    guild_id,
                )

            if category == "text":
                return await leaderboard_service.get_all_text_channel_leaderboard(
                    self.bot.db_pool,
                    guild_id,
                )

            if category == "voicechannel":
                return await leaderboard_service.get_all_voice_channel_leaderboard(
                    self.bot.db_pool,
                    guild_id,
                )

        if category == "messages":
            return await leaderboard_service.get_message_leaderboard(
                self.bot.db_pool,
                guild_id,
                period,
            )

        if category == "voice":
            return await leaderboard_service.get_voice_leaderboard(
                self.bot.db_pool,
                guild_id,
                period,
            )

        if category == "text":
            return await leaderboard_service.get_text_channel_leaderboard(
                self.bot.db_pool,
                guild_id,
                period,
            )

        if category == "voicechannel":
            return await leaderboard_service.get_voice_channel_leaderboard(
                self.bot.db_pool,
                guild_id,
                period,
            )

        return []


    def _build_embed(
        self,
        guild: discord.Guild,
        category: str,
        period: str | None,
        results,
    ) -> discord.Embed:
        """Build the RAXOR leaderboard embed."""

        medals = {
            1: "🥇",
            2: "🥈",
            3: "🥉",
        }

        # =========================
        # Level Leaderboard
        # =========================


        if category == "level":
            embed = leaderboard_embed(
                "Level Leaderboard",
                "Server members ranked by current level.",
            )

            for position, row in enumerate(results[:10], start=1):
                user_id = row["user_id"]
                level = row["level"]
                xp = row["xp"]

                member = guild.get_member(user_id)

                if member is not None:
                    name = member.display_name
                    mention = member.mention
                else:
                    name = f"User {user_id}"

                rank_prefix = medals.get(
                    position,
                    f"`#{position}`",
                )

                embed.add_field(
                    name=f"{rank_prefix}. {name}",
                    value=(
                        f"{mention}\n"
                        f"**Level:** `{format_number(level)}`\n"
                        f"**XP:** `{format_number(xp)}`"
                    ),
                    inline=False,
                )

            embed.set_footer(
                text="RAXOR • Top 10 • All-time level ranking"
            )

            return embed

        # =========================
        # Leaderboard Titles
        # =========================


        titles = {
            "messages": "Message Leaderboard",
            "voice": "Voice Time Leaderboard",
            "text": "Text Channel Leaderboard",
            "voicechannel": "Voice Channel Leaderboard",
        }

        descriptions = {
            "messages": "Members ranked by message activity.",
            "voice": "Members ranked by counted voice time.",
            "text": "Text channels ranked by message activity.",
            "voicechannel": "Voice channels ranked by active voice time.",
        }

        embed = leaderboard_embed(
            titles[category],
            descriptions[category],
        )


        # =========================
        # Messages
        # =========================


        if category == "messages":
            for position, row in enumerate(
                results[:10],
                start=1,
            ):
                user_id = row["user_id"]
                message_count = row["message_count"]

                member = guild.get_member(user_id)

                if member is not None:
                    name = member.display_name
                    mention = member.mention
                else:
                    name = f"User {user_id}"
                    mention = name

                rank_prefix = medals.get(
                    position,
                    f"`#{position}`",
                )


                embed.add_field(
                    name=f"{rank_prefix}. {name}",
                    value=(
                        f"{mention}\n"
                        f"**Messages:** "
                        f"`{format_number(message_count)}`"
                    ),
                    inline=False,
                )


        # =========================
        # Voice
        # =========================

        elif category == "voice":
            for position, row in enumerate(
                results[:10],
                start=1,
            ):
                user_id = row["user_id"]
                voice_seconds = row["voice_seconds"]

                member = guild.get_member(user_id)

                if member is not None:
                    name = member.display_name
                    mention = member.mention
                else:
                    name = f"User {user_id}"
                    mention = name

                rank_prefix = medals.get(
                    position,
                    f"`#{position}`",
                )


                embed.add_field(
                    name=f"{rank_prefix}. {name}",
                    value=(
                        f"{mention}\n"
                        f"**Voice Time:** "
                        f"`{format_duration(voice_seconds)}`"
                    ),
                    inline=False,
                )


        # =========================
        # Text Channels
        # =========================


        elif category == "text":
            for position, row in enumerate(
                results[:10],
                start=1,
            ):
                channel_id = row["channel_id"]
                message_count = row["message_count"]

                channel = guild.get_channel(channel_id)

                if channel is not None:
                    name = channel.name
                    mention = channel.mention
                else:
                    name = f"Channel {channel_id}"
                    mention = name

                rank_prefix = medals.get(
                    position,
                    f"`{position}`",
                )

                embed.add_field(
                    name=f"{rank_prefix}. #{name}",
                    value=(
                        f"{mention}\n"
                        f"**Messages:** "
                        f"`{format_number(message_count)}`"
                    ),
                    inline=False,
                )


        # =========================
        # Voice Channels
        # =========================


        elif category == "voicechannel":
            for position, row in enumerate(
                results[:10],
                start=1,
            ):
                channel_id = row["channel_id"]
                voice_seconds = row["voice_seconds"]

                channel = guild.get_channel(channel_id)

                if channel is not None:
                    name = channel.name
                    mention = channel.mention
                else:
                    name = f"Channel {channel_id}"
                    mention = name

                rank_prefix = medals.get(
                    position,
                    f"`{position}`",
                )

                embed.add_field(
                    name=f"{rank_prefix}. 🔊 {name}",
                    value=(
                        f"{mention}\n"
                        f"**Active Time:** "
                        f"`{format_duration(voice_seconds)}`"
                    ),
                    inline=False,
                )

        # =========================
        # Footer
        # =========================

        if period == "all":
            period_text = "ALL-TIME"
        else:
            period_text = period.upper()

        embed.set_footer(
            text=f"RAXOR • Top 10 • {period_text}"
        )

        return embed



    async def _execute_rank(
        self,
        guild: discord.Guild,
        category: str,
        period: str | None,
    ) -> discord.Embed:
        """Execute the common leaderboard logic."""

        valid_categories = {
            "messages",
            "voice",
            "text",
            "voicechannel",
            "level",
        }

        if category not in valid_categories:
            raise ValueError("Invalid leaderboard category.")

        if category == "level":
            if period is not None:
                raise ValueError(
                    "Level leaderboard does not use a period."
                )
        else:
            valid_periods = {
                "daily",
                "weekly",
                "monthly",
                "all",
            }

            if period is None:
                raise ValueError(
                    "Please specify a period: "
                    "daily, weekly, monthly, or all."
                )

            if period not in valid_periods:
                raise ValueError(
                    "Invalid period. Use daily, weekly, monthly, or all."
                )

        results = await self._get_results(
            guild.id,
            category,
            period,
        )

        if not results:
            embed = leaderboard_embed(
                (
                    "Level Leaderboard"
                    if category == "level"
                    else {
                        "messages": "Message Leaderboard",
                        "voice": "Voice Time Leaderboard",
                        "text": "Text Channel Leaderboard",
                        "voicechannel": "Voice Channel Leaderboard",
                    }[category]
                ),
                "No leaderboard data available yet.",
            )

            if category == "level":
                embed.set_footer(
                    text="Top 10 • All-time level ranking"
                )
            elif period == "all":
                embed.set_footer(
                    text="Top 10 • All-time"
                )
            else:
                embed.set_footer(
                    text=f"Top 10 • {period.capitalize()}"
                )

            return embed

        return self._build_embed(
            guild,
            category,
            period,
            results,
        )


    @commands.command(name="rank")
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def rank(
        self,
        ctx: commands.Context,
        category: str = None,
        period: str = None,
    ):
        """Show leaderboard rankings using the prefix command."""

        if ctx.guild is None:
            await ctx.send(
                embed=error_embed(
                    "Leaderboard",
                    "This command can only be used inside a server.",
                )
            )
            return

        if category is None:
            await ctx.send(
                embed=error_embed(
                    "Leaderboard",
                    (
                        "Usage: `₹rank "
                        "<messages|voice|text|voicechannel|level> [period]`"
                    ),
                )
            )
            return

        category = category.lower()

        if period is not None:
            period = period.lower()

        try:
            embed = await self._execute_rank(
                ctx.guild,
                category,
                period,
            )

        except ValueError as error:
            await ctx.send(
                embed=error_embed(
                    "Leaderboard",
                    str(error),
                )
            )
            return

        await ctx.send(embed=embed)


    @app_commands.command(
        name="rank",
        description="Show leaderboard rankings.",
    )
    @app_commands.checks.cooldown(2, 5, key=lambda i: i.user.id)
    @app_commands.describe(
        category="Leaderboard category.",
        period="Leaderboard period. Not used for level.",
    )
    @app_commands.choices(
        category=[
            app_commands.Choice(
                name="Messages",
                value="messages",
            ),
            app_commands.Choice(
                name="Voice Time",
                value="voice",
            ),
            app_commands.Choice(
                name="Text Channels",
                value="text",
            ),
            app_commands.Choice(
                name="Voice Channels",
                value="voicechannel",
            ),
            app_commands.Choice(
                name="Level",
                value="level",
            ),
        ],
        period=[
            app_commands.Choice(
                name="Daily",
                value="daily",
            ),
            app_commands.Choice(
                name="Weekly",
                value="weekly",
            ),
            app_commands.Choice(
                name="Monthly",
                value="monthly",
            ),
            app_commands.Choice(
                name="All-time",
                value="all",
            ),
        ],
    )
    async def slash_rank(
        self,
        interaction: discord.Interaction,
        category: app_commands.Choice[str],
        period: app_commands.Choice[str] | None = None,
    ):
        """Show leaderboard rankings using the slash command."""

        if interaction.guild is None:
            await interaction.response.send_message(
                embed=error_embed(
                    "Leaderboard",
                    "This command can only be used inside a server.",
                ),
                ephemeral=True,
            )
            return

        selected_category = category.value
        selected_period = (
            period.value
            if period is not None
            else None
        )

        try:
            embed = await self._execute_rank(
                interaction.guild,
                selected_category,
                selected_period,
            )

        except ValueError as error:
            await interaction.response.send_message(
                embed=error_embed(
                    "Leaderboard",
                    str(error),
                ),
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            embed=embed
        )


async def setup(bot):
    """Load the leaderboard cog."""

    await bot.add_cog(Leaderboard(bot))

