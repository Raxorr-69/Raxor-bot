import discord

from discord.ext import commands

from bot.checks import admin_only

from database.repositories import (
    get_guild,
    create_guild,
    update_guild_setting,
)

from utils.embeds import (
    error_embed,
    normal_embed,
    success_embed,
)

class AutoMod(commands.Cog):
    """Auto-moderation configuration commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="automod")
    @admin_only()
    @commands.guild_only()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def automod(
        self,
        ctx: commands.Context,
        setting: str,
        value: str,
    ):
        """Enable or disable an AutoMod protection."""

        allowed_settings = {
            "spam": "spam_enabled",
            "links": "link_protection_enabled",
        }

        setting = setting.lower()
        value = value.lower()

        if setting not in allowed_settings:
            await ctx.send(
                embed=error_embed(
                    title="AutoMod",
                    description="Invalid setting. Use `spam` or `links`.",
                )
            )
            return

        if value not in {"on", "off"}:
            await ctx.send(
                embed=error_embed(
                    title="AutoMod",
                    description="Invalid value. Use `on` or `off`.",
                )
            )
            return

        guild = await get_guild(
            self.bot.db_pool,
            ctx.guild.id,
        )

        if guild is None:
            await create_guild(
                self.bot.db_pool,
                ctx.guild.id,
            )

        await update_guild_setting(
            self.bot.db_pool,
            ctx.guild.id,
            allowed_settings[setting],
            value == "on",
        )

        status = "enabled" if value == "on" else "disabled"

        await ctx.send(
            embed=success_embed(
                title="AutoMod",
                description=f"AutoMod `{setting}` has been {status}.",
            )
        )

    @commands.hybrid_command(name="spamconfig")
    @admin_only()
    @commands.guild_only()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def spamconfig(
        self,
        ctx: commands.Context,
        message_limit: int,
        window_seconds: int,
    ):
        """Configure message spam detection."""

        if message_limit <= 0:
            await ctx.send(
                embed=error_embed(
                    title="Spam Configuration",
                    description="Message limit must be greater than 0.",
                )
            )
            return

        if window_seconds <= 0:
            await ctx.send(
                embed=error_embed(
                    title="Spam Configuration",
                    description="Time window must be greater than 0 seconds.",
                )
            )
            return

        guild = await get_guild(
            self.bot.db_pool,
            ctx.guild.id,
        )

        if guild is None:
            await create_guild(
                self.bot.db_pool,
                ctx.guild.id,
            )

        await update_guild_setting(
            self.bot.db_pool,
            ctx.guild.id,
            "spam_message_limit",
            message_limit,
        )

        await update_guild_setting(
            self.bot.db_pool,
            ctx.guild.id,
            "spam_message_window",
            window_seconds,
        )

        await ctx.send(
            embed=success_embed(
                title="Spam Configuration",
                description=(
                    f"Message spam limit set to `{message_limit}` "
                    f"messages per `{window_seconds}` seconds."
                ),
            )
        )


    @commands.hybrid_command(name="spamaction")
    @admin_only()
    @commands.guild_only()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def spamaction(
        self,
        ctx: commands.Context,
        action: str,
        timeout_seconds: int = 60,
    ):
        """Configure what happens when message spam is detected."""

        action = action.lower()

        allowed_actions = {
            "warn",
            "delete",
            "timeout",
        }

        if action not in allowed_actions:
            await ctx.send(
                embed=error_embed(
                    title="Spam Action",
                    description=(
                        "Invalid action.\n\n"
                        "Allowed actions: `warn`, `delete`, `timeout`."
                    ),
                )
            )
            return

        if timeout_seconds <= 0:
            await ctx.send(
                embed=error_embed(
                    title="Spam Action",
                    description="Timeout duration must be greater than 0 seconds.",
                )
            )
            return

        guild = await get_guild(
            self.bot.db_pool,
            ctx.guild.id,
        )

        if guild is None:
            await create_guild(
                self.bot.db_pool,
                ctx.guild.id,
            )

        try:
            await update_guild_setting(
                self.bot.db_pool,
                ctx.guild.id,
                "spam_action",
                action,
            )

            await update_guild_setting(
                self.bot.db_pool,
                ctx.guild.id,
                "spam_timeout_seconds",
                timeout_seconds,
            )
        except ValueError as exc:
            await ctx.send(
                embed=error_embed(
                    title="Spam Action",
                    description=str(exc),
                )
            )
            return

        await ctx.send(
            embed=success_embed(
                title="Spam Action Updated",
                description=(
                    f"Action: `{action}`\n"
                    f"Timeout duration: `{timeout_seconds}` seconds"
                ),
            )
        )

    @commands.hybrid_command(name="emojiconfig")
    @admin_only()
    @commands.guild_only()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def emojiconfig(
        self,
        ctx: commands.Context,
        limit: int,
        action: str = "warn",
        timeout_seconds: int = 60,
    ):
        """Configure emoji spam detection: limit, action, and timeout."""

        action = action.lower()

        allowed_actions = {
            "warn",
            "delete",
            "timeout",
        }

        if limit <= 0:
            await ctx.send(
                embed=error_embed(
                    title="Emoji Spam Configuration",
                    description="Emoji limit must be greater than 0.",
                )
            )
            return

        if action not in allowed_actions:
            await ctx.send(
                embed=error_embed(
                    title="Emoji Spam Configuration",
                    description=(
                        "Invalid action.\n\n"
                        "Allowed actions: `warn`, `delete`, `timeout`."
                    ),
                )
            )
            return

        if timeout_seconds <= 0:
            await ctx.send(
                embed=error_embed(
                    title="Emoji Spam Configuration",
                    description="Timeout duration must be greater than 0 seconds.",
                )
            )
            return

        guild = await get_guild(
            self.bot.db_pool,
            ctx.guild.id,
        )

        if guild is None:
            await create_guild(
                self.bot.db_pool,
                ctx.guild.id,
            )

        try:
            await update_guild_setting(
                self.bot.db_pool,
                ctx.guild.id,
                "emoji_spam_limit",
                limit,
            )

            await update_guild_setting(
                self.bot.db_pool,
                ctx.guild.id,
                "emoji_spam_action",
                action,
            )

            await update_guild_setting(
                self.bot.db_pool,
                ctx.guild.id,
                "emoji_spam_timeout_seconds",
                timeout_seconds,
            )
        except ValueError as exc:
            await ctx.send(
                embed=error_embed(
                    title="Emoji Spam Configuration",
                    description=str(exc),
                )
            )
            return

        await ctx.send(
            embed=success_embed(
                title="Emoji Spam Configuration Updated",
                description=(
                    f"Emoji limit: `{limit}`\n"
                    f"Action: `{action}`\n"
                    f"Timeout duration: `{timeout_seconds}` seconds"
                ),
            )
        )

    @commands.hybrid_command(name="linkconfig")
    @admin_only()
    @commands.guild_only()
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def linkconfig(
        self,
        ctx: commands.Context,
        action: str,
        timeout_seconds: int = 60,
    ):
        """Configure link protection action and timeout duration."""

        action = action.lower()

        allowed_actions = {
            "warn",
            "delete",
            "timeout",
        }

        if action not in allowed_actions:
            await ctx.send(
                embed=error_embed(
                    "Link Protection",
                    (
                        "Invalid action.\n\n"
                        "Allowed actions: `warn`, `delete`, `timeout`."
                    ),
                )
            )
            return

        if timeout_seconds <= 0:
            await ctx.send(
                embed=error_embed(
                    "Link Protection",
                    "Timeout duration must be greater than `0` seconds.",
                )
            )
            return

        pool = ctx.bot.db_pool

        try:
            await update_guild_setting(
                pool,
                ctx.guild.id,
                "link_action",
                action,
            )

            await update_guild_setting(
                pool,
                ctx.guild.id,
                "link_timeout_seconds",
                timeout_seconds,
            )

        except ValueError as exc:
            await ctx.send(
                embed=error_embed(
                    "Link Protection",
                str(exc),
                )
            )
            return

        await ctx.send(
            embed=success_embed(
                "Link Protection Updated",
                (
                    f"Action: `{action}`\n"
                    f"Timeout duration: `{timeout_seconds}` seconds"
                ),
            )
        )



async def setup(bot):
    """Load the AutoMod command cog."""
    await bot.add_cog(AutoMod(bot))
