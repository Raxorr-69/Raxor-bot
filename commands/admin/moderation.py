import datetime

import discord
from discord.ext import commands

from bot.checks import admin_only
from database.repositories import add_warning
from utils.embeds import moderation_embed
from utils.formatters import truncate_field


class ConfirmBanView(discord.ui.View):
    """Confirmation prompt shown before an irreversible ban."""

    def __init__(self, author_id: int, timeout: float = 15.0):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.confirmed: bool | None = None

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        # Only the person who ran the command can confirm/cancel it.
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                embed=moderation_embed(
                    title="Confirm Ban",
                    description=(
                        "Only the person who ran this command can confirm it."
                    ),
                ),
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Confirm Ban", style=discord.ButtonStyle.danger)
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        self.confirmed = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        self.confirmed = False
        self.stop()
        await interaction.response.defer()

    async def on_timeout(self) -> None:
        self.confirmed = False


class Moderation(commands.Cog):
    """Administrative moderation commands."""

    def __init__(self, bot):
        self.bot = bot

    def can_moderate(
        self,
        ctx: commands.Context,
        member: discord.Member,
    ) -> bool:
        """Check whether the moderator and bot can moderate a member."""

        if member == ctx.guild.owner:
            return False

        # The server owner always outranks every role in the server,
        # even without an elevated role of their own — otherwise an
        # owner with no special role could never moderate anyone.
        is_owner = ctx.author.id == ctx.guild.owner_id

        if not is_owner and member.top_role >= ctx.author.top_role:
            return False

        if member.top_role >= ctx.guild.me.top_role:
            return False

        return True

    @commands.hybrid_command(name="warn")
    @admin_only()
    @commands.guild_only()
    @commands.cooldown(3, 10, commands.BucketType.user)
    async def warn(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided",
    ):
        """Warn a server member."""

        if member.bot:
            await ctx.send(
                embed=moderation_embed(
                    title="Warning",
                    description="Bots cannot be warned.",
                )
            )
            return

        if member.id == ctx.author.id:
            await ctx.send(
                embed=moderation_embed(
                    title="Warning",
                    description="You cannot warn yourself.",
                )
            )
            return

        if member == ctx.guild.owner:
            await ctx.send(
                embed=moderation_embed(
                    title="Warning",
                    description="The server owner cannot be warned.",
                )
            )
            return

        # The server owner always outranks every role in the server,
        # even without an elevated role of their own.
        author_is_owner = ctx.author.id == ctx.guild.owner_id

        if not author_is_owner and member.top_role >= ctx.author.top_role:
            await ctx.send(
                embed=moderation_embed(
                    title="Warning",
                    description=(
                        "You cannot warn a member with an equal or higher role."
                    ),
                )
            )
            return

        await add_warning(
            self.bot.db_pool,
            guild_id=ctx.guild.id,
            user_id=member.id,
            moderator_id=ctx.author.id,
            reason=reason,
        )

        await ctx.send(
            embed=moderation_embed(
                title="Member Warned",
                description=f"{member.mention} has been warned.",
                fields=[
                    ("Reason", truncate_field(reason), False),
                ],
            )
        )

    @commands.hybrid_command(name="kick")
    @admin_only()
    @commands.guild_only()
    @commands.cooldown(3, 10, commands.BucketType.user)
    async def kick(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided",
    ):
        """Kick a server member."""

        if member.bot:
            await ctx.send(
                embed=moderation_embed(
                    title="Kick",
                    description="Bots cannot be kicked.",
                )
            )
            return

        if member.id == ctx.author.id:
            await ctx.send(
                embed=moderation_embed(
                    title="Kick",
                    description="You cannot kick yourself.",
                )
            )
            return

        if member == ctx.guild.owner:
            await ctx.send(
                embed=moderation_embed(
                    title="Kick",
                    description="The server owner cannot be kicked.",
                )
            )
            return

        if not self.can_moderate(ctx, member):
            await ctx.send(
                embed=moderation_embed(
                    title="Kick",
                    description=(
                        "I cannot moderate this member because of role hierarchy."
                    ),
                )
            )
            return

        try:
            await member.kick(reason=reason)
        except discord.Forbidden:
            await ctx.send(
                embed=moderation_embed(
                    title="Kick",
                    description="I don't have permission to kick this member.",
                )
            )
            return
        except discord.HTTPException:
            await ctx.send(
                embed=moderation_embed(
                    title="Kick",
                    description="I couldn't kick this member.",
                )
            )
            return

        await ctx.send(
            embed=moderation_embed(
                title="Member Kicked",
                description=f"{member.mention} has been kicked.",
                fields=[
                    ("Reason", truncate_field(reason), False),
                ],
            )
        )

    @commands.hybrid_command(name="timeout")
    @admin_only()
    @commands.guild_only()
    @commands.cooldown(3, 10, commands.BucketType.user)
    async def timeout(
        self,
        ctx: commands.Context,
        member: discord.Member,
        duration: int,
        *,
        reason: str = "No reason provided",
    ):
        """Timeout a server member."""

        if member.bot:
            await ctx.send(
                embed=moderation_embed(
                    title="Timeout",
                    description="Bots cannot be timed out.",
                )
            )
            return

        if member.id == ctx.author.id:
            await ctx.send(
                embed=moderation_embed(
                    title="Timeout",
                    description="You cannot timeout yourself.",
                )
            )
            return

        if member == ctx.guild.owner:
            await ctx.send(
                embed=moderation_embed(
                    title="Timeout",
                    description="The server owner cannot be timed out.",
                )
            )
            return

        if not self.can_moderate(ctx, member):
            await ctx.send(
                embed=moderation_embed(
                    title="Timeout",
                    description=(
                        "I cannot moderate this member because of role hierarchy."
                    ),
                )
            )
            return

        if duration <= 0:
            await ctx.send(
                embed=moderation_embed(
                    title="Timeout",
                    description=(
                        "Timeout duration must be greater than 0 seconds."
                    ),
                )
            )
            return

        try:
            await member.timeout(
                datetime.timedelta(seconds=duration),
                reason=reason,
            )
        except discord.Forbidden:
            await ctx.send(
                embed=moderation_embed(
                    title="Timeout",
                    description=(
                        "I don't have permission to timeout this member."
                    ),
                )
            )
            return
        except discord.HTTPException:
            await ctx.send(
                embed=moderation_embed(
                    title="Timeout",
                    description="I couldn't timeout this member.",
                )
            )
            return

        await ctx.send(
            embed=moderation_embed(
                title="Member Timed Out",
                description=(
                    f"{member.mention} has been timed out for "
                    f"{duration} seconds."
                ),
                fields=[
                    ("Reason", truncate_field(reason), False),
                ],
            )
        )

    @commands.hybrid_command(name="ban")
    @admin_only()
    @commands.guild_only()
    @commands.cooldown(2, 10, commands.BucketType.user)
    async def ban(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided",
    ):
        """Ban a server member."""

        if member.bot:
            await ctx.send(
                embed=moderation_embed(
                    title="Ban",
                    description="Bots cannot be banned.",
                )
            )
            return

        if member.id == ctx.author.id:
            await ctx.send(
                embed=moderation_embed(
                    title="Ban",
                    description="You cannot ban yourself.",
                )
            )
            return

        if member == ctx.guild.owner:
            await ctx.send(
                embed=moderation_embed(
                    title="Ban",
                    description="The server owner cannot be banned.",
                )
            )
            return

        if not self.can_moderate(ctx, member):
            await ctx.send(
                embed=moderation_embed(
                    title="Ban",
                    description=(
                        "I cannot moderate this member because of role hierarchy."
                    ),
                )
            )
            return

        # Bans are irreversible, so require an explicit confirmation
        # before actually removing the member from the server.
        view = ConfirmBanView(author_id=ctx.author.id)
        confirm_message = await ctx.send(
            embed=moderation_embed(
                title="Confirm Ban",
                description=(
                    f"Are you sure you want to ban {member.mention}?\n\n"
                    f"**Reason:** {reason}"
                ),
            ),
            view=view,
        )

        await view.wait()

        if not view.confirmed:
            await confirm_message.edit(
                embed=moderation_embed(
                    title="Ban Cancelled",
                    description=f"Ban on {member.mention} was cancelled or timed out.",
                ),
                view=None,
            )
            return

        try:
            await member.ban(reason=reason)
        except discord.Forbidden:
            await confirm_message.edit(
                embed=moderation_embed(
                    title="Ban",
                    description="I don't have permission to ban this member.",
                ),
                view=None,
            )
            return
        except discord.HTTPException:
            await confirm_message.edit(
                embed=moderation_embed(
                    title="Ban",
                    description="I couldn't ban this member.",
                ),
                view=None,
            )
            return

        await confirm_message.edit(view=None)

        await ctx.send(
            embed=moderation_embed(
                title="Member Banned",
                description=f"{member.mention} has been banned.",
                fields=[
                    ("Reason", truncate_field(reason), False),
                ],
            )
        )


async def setup(bot):
    """Load the moderation command cog."""
    await bot.add_cog(Moderation(bot))
