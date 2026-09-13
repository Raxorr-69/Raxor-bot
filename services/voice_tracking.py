from datetime import datetime, timedelta, timezone

from database.repositories import (
    add_voice_time,
    create_user,
    increment_daily_channel_voice_stat,
)


# =========================
# Active User Voice Sessions
# =========================

user_voice_sessions = {}


# =========================
# Active Voice Channel Sessions
# =========================

voice_channel_sessions = {}


# =========================
# User Voice Session
# =========================


def start_user_voice_session(
    guild_id: int,
    user_id: int,
    channel_id: int,
    deafened: bool = False,
):
    """Start tracking a user's voice session."""

    now = datetime.now(timezone.utc)

    user_voice_sessions[(guild_id, user_id)] = {
        "channel_id": channel_id,
        "started_at": now,
        "deafened": deafened,
        "counted_started_at": (
            None if deafened else now
        ),
    }


def get_user_voice_session(
    guild_id: int,
    user_id: int,
):
    """Get a user's active voice session."""

    return user_voice_sessions.get(
        (guild_id, user_id)
    )


def remove_user_voice_session(
    guild_id: int,
    user_id: int,
):
    """Remove a user's active voice session."""

    return user_voice_sessions.pop(
        (guild_id, user_id),
        None,
    )


# =========================
# Deafen Handling
# =========================


def update_user_deafen_status(
    guild_id: int,
    user_id: int,
    deafened: bool,
):
    """Update a user's deafen state."""

    session = get_user_voice_session(
        guild_id,
        user_id,
    )

    if session is None:
        return

    session["deafened"] = deafened

    if deafened:
        session["counted_started_at"] = None
    else:
        session["counted_started_at"] = (
            datetime.now(timezone.utc)
        )


# =========================
# Voice Channel Session
# =========================


def start_voice_channel_session(
    guild_id: int,
    channel_id: int,
):
    """Start tracking a voice channel's active session."""

    key = (guild_id, channel_id)

    # Do not overwrite an existing session.
    if key not in voice_channel_sessions:

        voice_channel_sessions[key] = (
            datetime.now(timezone.utc)
        )


def get_voice_channel_session(
    guild_id: int,
    channel_id: int,
):
    """Get a voice channel's active session."""

    return voice_channel_sessions.get(
        (guild_id, channel_id)
    )


def remove_voice_channel_session(
    guild_id: int,
    channel_id: int,
):
    """Remove a voice channel's active session."""

    return voice_channel_sessions.pop(
        (guild_id, channel_id),
        None,
    )


# =========================
# Duration Calculation
# =========================


def calculate_seconds(
    started_at: datetime,
    ended_at: datetime,
):
    """Calculate duration between two UTC timestamps."""

    if ended_at <= started_at:
        return 0

    return int(
        (ended_at - started_at).total_seconds()
    )


# =========================
# Split Duration By Date
# =========================


def split_duration_by_date(
    started_at: datetime,
    ended_at: datetime,
):
    """
    Split a duration across UTC calendar dates.

    Example:
    23:50 -> 00:10

    Becomes:
    Day 1 = 10 minutes
    Day 2 = 10 minutes
    """

    if ended_at <= started_at:
        return []

    parts = []

    current = started_at

    while current.date() < ended_at.date():

        next_day = datetime.combine(
            current.date() + timedelta(days=1),
            datetime.min.time(),
            tzinfo=timezone.utc,
        )

        seconds = calculate_seconds(
            current,
            next_day,
        )

        if seconds > 0:
            parts.append(
                (
                    current.date(),
                    seconds,
                )
            )

        current = next_day

    seconds = calculate_seconds(
        current,
        ended_at,
    )

    if seconds > 0:
        parts.append(
            (
                current.date(),
                seconds,
            )
        )

    return parts


# =========================
# Save User Voice Time
# =========================


async def save_user_voice_time(
    pool,
    guild_id: int,
    user_id: int,
    channel_id: int,
    started_at: datetime,
    ended_at: datetime,
):
    """
    Save a user's counted voice time.

    Deafened time should never be passed
    into this function.
    """

    if ended_at <= started_at:
        return

    for statistic_date, seconds in (
        split_duration_by_date(
            started_at,
            ended_at,
        )
    ):

        await add_voice_time(
            pool,
            user_id,
            guild_id,
            channel_id,
            statistic_date,
            seconds,
        )


# =========================
# Save Voice Channel Time
# =========================


async def save_voice_channel_time(
    pool,
    guild_id: int,
    channel_id: int,
    started_at: datetime,
    ended_at: datetime,
):
    """
    Save active voice-channel usage.

    This is independent of member
    deafen status.
    """

    if ended_at <= started_at:
        return

    for statistic_date, seconds in (
        split_duration_by_date(
            started_at,
            ended_at,
        )
    ):

        await increment_daily_channel_voice_stat(
            pool,
            guild_id,
            channel_id,
            statistic_date,
            seconds,
        )


# =========================
# Ensure User Exists
# =========================


async def ensure_voice_user(
    pool,
    guild_id: int,
    user_id: int,
):
    """Make sure a voice user has a database record."""

    await create_user(
        pool,
        user_id,
        guild_id,
    )


