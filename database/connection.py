import asyncpg

from config.settings import DATABASE_URL

from database.models import (
    USERS_TABLE,
    GUILDS_TABLE,
    CHANNEL_RULES_TABLE,
    STATISTICS_EXCLUDED_CHANNELS_TABLE,
    WHITELISTS_TABLE,
    AFK_TABLE,
    INVITES_TABLE,
    LEVEL_REWARDS_TABLE,
    LEADERBOARD_REWARDS_TABLE,
    MESSAGE_STATISTICS_TABLE,
    VOICE_STATISTICS_TABLE,
    CHANNEL_MESSAGE_STATISTICS_TABLE,
    CHANNEL_VOICE_STATISTICS_TABLE,
    PROCESSED_MESSAGES_TABLE,
    MESSAGE_RECOVERY_STATE_TABLE,
    RECOVERY_REQUESTS_TABLE,
    WARNING_HISTORY_TABLE,
    STATISTICS_INDEXES,
)


# =========================
# Database Connection Pool
# =========================

async def create_database_pool():
    """Create and return a PostgreSQL connection pool."""

    return await asyncpg.create_pool(
        DATABASE_URL,
        min_size=1,
        max_size=10,
        command_timeout=30,
        max_inactive_connection_lifetime=300,
    )


# =========================
# Database Initialization
# =========================

async def initialize_database(pool):
    """Create all required PostgreSQL tables."""

    async with pool.acquire() as connection:

        await connection.execute(USERS_TABLE)
        await connection.execute(GUILDS_TABLE)
        # Idempotent migration for databases created before verification settings existed.
        await connection.execute("ALTER TABLE guilds ADD COLUMN IF NOT EXISTS verification_enabled BOOLEAN NOT NULL DEFAULT FALSE")
        await connection.execute("ALTER TABLE guilds ADD COLUMN IF NOT EXISTS verification_channel_id BIGINT")
        await connection.execute("ALTER TABLE guilds ADD COLUMN IF NOT EXISTS verification_role_id BIGINT")
        await connection.execute("ALTER TABLE guilds ADD COLUMN IF NOT EXISTS welcome_enabled BOOLEAN NOT NULL DEFAULT FALSE")
        await connection.execute("ALTER TABLE guilds ADD COLUMN IF NOT EXISTS welcome_channel_id BIGINT")
        await connection.execute("ALTER TABLE guilds ADD COLUMN IF NOT EXISTS welcome_message TEXT NOT NULL DEFAULT 'Welcome {user} to {server}! 🎉'")
        await connection.execute("ALTER TABLE guilds ADD COLUMN IF NOT EXISTS welcome_gif_url TEXT")
        await connection.execute("ALTER TABLE guilds ADD COLUMN IF NOT EXISTS leave_enabled BOOLEAN NOT NULL DEFAULT FALSE")
        await connection.execute("ALTER TABLE guilds ADD COLUMN IF NOT EXISTS leave_channel_id BIGINT")
        await connection.execute("ALTER TABLE guilds ADD COLUMN IF NOT EXISTS leave_message TEXT NOT NULL DEFAULT '{username} has left {server}. 👋'")
        await connection.execute("ALTER TABLE guilds ADD COLUMN IF NOT EXISTS leave_gif_url TEXT")
        await connection.execute("ALTER TABLE guilds ADD COLUMN IF NOT EXISTS level_up_message TEXT NOT NULL DEFAULT '{user} reached **Level {level}**! 🎉'")
        await connection.execute("ALTER TABLE guilds ADD COLUMN IF NOT EXISTS level_up_gif_url TEXT")

        await connection.execute(CHANNEL_RULES_TABLE)
        await connection.execute(
            STATISTICS_EXCLUDED_CHANNELS_TABLE
        )

        await connection.execute(WHITELISTS_TABLE)

        await connection.execute(AFK_TABLE)
        await connection.execute(INVITES_TABLE)

        await connection.execute(LEVEL_REWARDS_TABLE)
        await connection.execute(LEADERBOARD_REWARDS_TABLE)

        await connection.execute(MESSAGE_STATISTICS_TABLE)
        await connection.execute(VOICE_STATISTICS_TABLE)

        await connection.execute(
            CHANNEL_MESSAGE_STATISTICS_TABLE
        )
        await connection.execute(
            CHANNEL_VOICE_STATISTICS_TABLE
        )
        await connection.execute(PROCESSED_MESSAGES_TABLE)
        await connection.execute(MESSAGE_RECOVERY_STATE_TABLE)
        await connection.execute(RECOVERY_REQUESTS_TABLE)

        await connection.execute(WARNING_HISTORY_TABLE)

        # Safe, idempotent indexes for growing statistics/recovery tables.
        for index_query in STATISTICS_INDEXES:
            await connection.execute(index_query)
