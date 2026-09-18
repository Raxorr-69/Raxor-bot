import discord
from discord.ext import commands

from bot.command_loader import load_commands
from config.settings import TEST_GUILD_ID
from web.internal import VerificationView


intents = discord.Intents.default()

intents.members = True
intents.message_content = True
intents.voice_states = True


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

        if TEST_GUILD_ID:
            guild = discord.Object(id=TEST_GUILD_ID)

            self.tree.copy_global_to(guild=guild)

            synced = await self.tree.sync(guild=guild)

            print(
                f"Synced {len(synced)} commands "
                f"to test guild {TEST_GUILD_ID}"
            )
        else:
            synced = await self.tree.sync()

            print(f"Synced {len(synced)} global commands")


bot = DiscordBot()