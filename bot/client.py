import discord
from discord.ext import commands

from bot.command_loader import load_commands
from web.internal import VerificationView

from config.settings import TEST_GUILD_ID


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
    await load_commands(self)
    self.add_view(VerificationView())

    if TEST_GUILD_ID:
        guild = discord.Object(id=TEST_GUILD_ID)

        # Copy globally loaded commands into the test server
        self.tree.copy_global_to(guild=guild)

        synced = await self.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands to test guild {TEST_GUILD_ID}")
    else:
        synced = await self.tree.sync()
        print(f"Synced {len(synced)} global commands")
        


        await self.tree.sync()


# Create the bot instance
bot = DiscordBot()
