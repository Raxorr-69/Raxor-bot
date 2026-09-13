from datetime import date, datetime, timezone

from database.repositories import (
    create_user,
    get_guild,
    create_guild,
    record_message_statistics_once,
    is_statistics_channel_excluded,
)


# =========================
# Message Statistics
# =========================


async def record_message(
    pool,
    user_id: int,
    guild_id: int,
    channel_id: int,
    statistic_date: date,
    message_id: int | None = None,
    message_created_at: datetime | None = None,
):
    """Record message statistics with optional message-level deduplication."""

    # =========================
    # Message Tracking Check
    # =========================

    guild_settings = await get_guild(
        pool,
        guild_id,
    )

    if guild_settings is None:
        await create_guild(
            pool,
            guild_id,
        )

        guild_settings = await get_guild(
            pool,
            guild_id,
        )

    if guild_settings is None:
        return False

    # =========================
    # Channel Exclusion Check
    # =========================

    excluded = await is_statistics_channel_excluded(
        pool,
        guild_id,
        channel_id,
    )

    if excluded:
        return False

    # =========================
    # Message Statistics
    # =========================

    # Normal/live messages and recovered messages both provide
    # a message ID. The repository handles the atomic
    # processed-message claim + statistics update.
    if message_id is not None:
        if message_created_at is None:
            message_created_at = datetime.now(timezone.utc)
        return await record_message_statistics_once(
            pool,
            guild_id,
            user_id,
            channel_id,
            statistic_date,
            message_id,
            message_created_at,
        )

    # =========================
    # Legacy Fallback
    # =========================

    # Keep compatibility for any existing caller that has
    # not yet been updated to provide a Discord message ID.
    await create_user(
        pool,
        user_id,
        guild_id,
    )

    return False
