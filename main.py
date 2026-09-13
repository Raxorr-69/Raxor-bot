import asyncio

import bot.events

from bot.client import bot
from config.settings import DISCORD_TOKEN, PORT
from database.connection import (
    create_database_pool,
    initialize_database,
)
from web.app import start_web_server


# =========================
# Main Application
# =========================


async def main():
    """Start the database and Discord bot."""

    # Create PostgreSQL connection pool
    pool = await create_database_pool()
    web_runner = None

    try:
        # Create all required database tables
        await initialize_database(pool)

        # Store the database pool on the bot
        bot.db_pool = pool

        # Start the health-check web server (only if PORT is configured)
        if PORT:
            web_runner = await start_web_server(bot, port=int(PORT))

        # Start Discord bot
        await bot.start(DISCORD_TOKEN)

    finally:
        # Stop the optional health-check server before closing the database.
        if web_runner is not None:
            await web_runner.cleanup()

        # Close database connections when bot stops
        await pool.close()


# =========================
# Application Entry Point
# =========================


if __name__ == "__main__":
    asyncio.run(main())
