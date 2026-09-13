from database import repositories
from utils.time import (
    get_today_date,
    get_next_day_date,
    get_week_start_date,
    get_next_week_start_date,
    get_month_start_date,
    get_next_month_start_date,
)


def get_period_dates(period: str):
    """Get the start and end dates for a leaderboard period."""

    if period == "daily":
        start_date = get_today_date()
        end_date = get_next_day_date(start_date)

    elif period == "weekly":
        start_date = get_week_start_date()
        end_date = get_next_week_start_date(start_date)

    elif period == "monthly":
        start_date = get_month_start_date()
        end_date = get_next_month_start_date(start_date)

    else:
        raise ValueError("Invalid leaderboard period.")

    return start_date, end_date


async def get_message_leaderboard(
    pool,
    guild_id: int,
    period: str,
):
    """Get member message leaderboard for a period."""

    start_date, end_date = get_period_dates(period)

    return await repositories.get_daily_message_stats(
        pool,
        guild_id,
        start_date,
        end_date,
    )


async def get_voice_leaderboard(
    pool,
    guild_id: int,
    period: str,
):
    """Get member voice-time leaderboard for a period."""

    start_date, end_date = get_period_dates(period)

    return await repositories.get_daily_voice_stats(
        pool,
        guild_id,
        start_date,
        end_date,
    )


async def get_all_message_leaderboard(
    pool,
    guild_id: int,
):
    """Get all-time member message leaderboard."""

    return await repositories.get_all_message_stats(
        pool,
        guild_id,
    )


async def get_all_voice_leaderboard(
    pool,
    guild_id: int,
):
    """Get all-time member voice-time leaderboard."""

    return await repositories.get_all_voice_stats(
        pool,
        guild_id,
    )


async def get_level_leaderboard(
    pool,
    guild_id: int,
):
    """Get all-time level leaderboard."""

    return await repositories.get_level_stats(
        pool,
        guild_id,
    )


async def get_text_channel_leaderboard(
    pool,
    guild_id: int,
    period: str,
):
    """Get text-channel message leaderboard for a period."""

    start_date, end_date = get_period_dates(period)

    return await repositories.get_daily_channel_message_stats(
        pool,
        guild_id,
        start_date,
        end_date,
    )


async def get_all_text_channel_leaderboard(
    pool,
    guild_id: int,
):
    """Get all-time text-channel leaderboard."""

    return await repositories.get_all_channel_message_stats(
        pool,
        guild_id,
    )


async def get_voice_channel_leaderboard(
    pool,
    guild_id: int,
    period: str,
):
    """Get voice-channel duration leaderboard for a period."""

    start_date, end_date = get_period_dates(period)

    return await repositories.get_daily_channel_voice_stats(
        pool,
        guild_id,
        start_date,
        end_date,
    )


async def get_all_voice_channel_leaderboard(
    pool,
    guild_id: int,
):
    """Get all-time voice-channel leaderboard."""

    return await repositories.get_all_channel_voice_stats(
        pool,
        guild_id,
    )


