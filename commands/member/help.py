from discord.ext import commands

from config.permissions import is_bot_owner
from utils.embeds import error_embed, normal_embed
from utils.formatters import truncate_field


# =========================
# Category Labels
# =========================

# Keys match the folder a command's module lives in
# (commands/<folder>/...), so new command files are
# picked up automatically without editing this file.
CATEGORY_LABELS = {
    "member": "Member",
    "info": "Information",
    "leaderboard": "Leaderboard",
    "admin": "Admin",
    "owner": "Owner",
    "developer": "Developer",
}

CATEGORY_ORDER = [
    "member",
    "info",
    "leaderboard",
    "admin",
    "owner",
    "developer",
]

# Categories that reveal privileged/internal commands and should
# only be shown to the bot developer, even though the commands
# themselves are already permission-gated. Listing them to everyone
# just hands out a map of admin/owner/developer functionality.
RESTRICTED_CATEGORIES = {"owner", "developer"}


def get_command_category(command: commands.Command) -> str:
    """Determine a command's category from the module it was defined in."""

    module = command.callback.__module__
    parts = module.split(".")

    if len(parts) >= 2 and parts[0] == "commands":
        return parts[1]

    return "general"


class Help(commands.Cog):
    """Custom help command."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="help")
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def help_command(
        self,
        ctx: commands.Context,
        *,
        command_name: str = None,
    ):
        """Show all available commands or details about one command."""

        prefix = ctx.prefix

        # =========================
        # Single Command Help
        # =========================

        if command_name is not None:
            command = self.bot.get_command(command_name.lower())

            is_restricted = (
                command is not None
                and get_command_category(command) in RESTRICTED_CATEGORIES
                and not is_bot_owner(ctx.author)
            )

            if command is None or command.hidden or is_restricted:
                await ctx.send(
                    embed=error_embed(
                        title="Help",
                        description=(
                            f"No command named `{command_name}` was found."
                        ),
                    )
                )
                return

            usage = f"{prefix}{command.qualified_name}"

            if command.signature:
                usage += f" {command.signature}"

            embed = normal_embed(
                title=f"Command: {command.qualified_name}",
                description=command.help or "No description provided.",
            )

            embed.add_field(
                name="Usage",
                value=f"`{usage}`",
                inline=False,
            )

            if command.aliases:
                embed.add_field(
                    name="Aliases",
                    value=", ".join(
                        f"`{alias}`" for alias in command.aliases
                    ),
                    inline=False,
                )

            await ctx.send(embed=embed)
            return

        # =========================
        # Full Command List
        # =========================

        categories: dict[str, list[str]] = {}

        author_is_owner = is_bot_owner(ctx.author)

        for command in self.bot.commands:
            if command.hidden:
                continue

            category = get_command_category(command)

            if category in RESTRICTED_CATEGORIES and not author_is_owner:
                continue

            categories.setdefault(category, []).append(command.name)

        embed = normal_embed(
            title="Raxor — Command List",
            description=(
                f"Use `{prefix}help <command>` for details about "
                "a specific command."
            ),
        )

        remaining = dict(categories)

        for category in CATEGORY_ORDER:
            names = remaining.pop(category, None)

            if not names:
                continue

            embed.add_field(
                name=CATEGORY_LABELS.get(category, category.title()),
                value=truncate_field(
                    ", ".join(f"`{name}`" for name in sorted(names))
                ),
                inline=False,
            )

        for category, names in sorted(remaining.items()):
            embed.add_field(
                name=CATEGORY_LABELS.get(category, category.title()),
                value=truncate_field(
                    ", ".join(f"`{name}`" for name in sorted(names))
                ),
                inline=False,
            )

        embed.set_footer(
            text="Some commands require admin, owner, or developer permissions."
        )

        await ctx.send(embed=embed)


async def setup(bot):
    """Load the help command cog."""
    await bot.add_cog(Help(bot))
