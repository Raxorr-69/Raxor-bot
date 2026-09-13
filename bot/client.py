import discord
from discord.ext import commands

from bot.command_loader import load_commands
from web.internal import VerificationView

# =========================
# Discord Intents
# =========================

intents = discord.Intents.default()

# Required for member-related features
intents.members = True

# Required for reading messages and message-based features
intents.message_content = True

# Required for voice tracking
intents.voice_states = True


# =========================
# Bot Client
# =========================

class DiscordBot(commands.Bot):
    """Main Discord bot."""

    def __init__(self):
        super().__init__(
            command_prefix="₹",
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self):
        """Load commands and sync slash commands."""

        await load_commands(self)
        self.add_view(VerificationView())

        await self.tree.sync()


# Create the bot instance
bot = DiscordBot()
