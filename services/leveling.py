import random
import time
import math
import weakref
import asyncio

from database import repositories


# --------------------------------------------------
# XP Cooldown Tracking
# --------------------------------------------------
#
# Prevents members from farming XP by spamming short messages.
# This is intentionally independent of any per-server spam-protection
# config, since that feature can be disabled while leveling stays on.

_last_xp_award = {}
XP_COOLDOWN_SECONDS = 60

_cleanup_counter = 0
_CLEANUP_INTERVAL = 500
_STALE_AFTER_SECONDS = 3600

# Per-user locks prevent two simultaneous messages from reading the same XP
# value and overwriting each other's update. Weak references keep this bounded
# without changing the public leveling API.
_xp_locks = weakref.WeakValueDictionary()

def _get_xp_lock(guild_id: int, user_id: int):
    key = (guild_id, user_id)
    lock = _xp_locks.get(key)
    if lock is None:
        lock = asyncio.Lock()
        _xp_locks[key] = lock
    return lock


def _is_on_xp_cooldown(guild_id: int, user_id: int, now: float) -> bool:
    """Check and record whether a user just earned XP within the cooldown."""

    global _cleanup_counter

    key = (guild_id, user_id)
    last_awarded = _last_xp_award.get(key)

    on_cooldown = (
        last_awarded is not None
        and (now - last_awarded) < XP_COOLDOWN_SECONDS
    )

    if not on_cooldown:
        _last_xp_award[key] = now

    _cleanup_counter += 1
    if _cleanup_counter >= _CLEANUP_INTERVAL:
        _cleanup_counter = 0
        _cleanup_stale_xp_entries(now)

    return on_cooldown


def _cleanup_stale_xp_entries(now: float) -> None:
    """Drop cooldown entries for users inactive for a long while."""

    stale_keys = [
        key
        for key, last_awarded in _last_xp_award.items()
        if (now - last_awarded) > _STALE_AFTER_SECONDS
    ]

    for key in stale_keys:
        _last_xp_award.pop(key, None)


# --------------------------------------------------
# Level progression
# --------------------------------------------------

BASE_XP = 100


def xp_required_for_level(level: int) -> int:
    """Return the total XP required to reach a level."""

    if level <= 0:
        return 0

    return BASE_XP * (level ** 2)


def calculate_level(total_xp: int) -> int:
    """Calculate the current level from total XP."""

    if total_xp <= 0:
        return 0

    # Requirements are BASE_XP * level^2, so the level is simply the
    # integer square root of total_xp / BASE_XP. This is O(1) instead of
    # looping once for every level.
    return math.isqrt(total_xp // BASE_XP)


def get_level_progress(total_xp: int) -> dict:
    """Return the current level and progress toward the next level."""

    level = calculate_level(total_xp)

    current_level_xp = xp_required_for_level(level)
    next_level_xp = xp_required_for_level(level + 1)

    progress_xp = total_xp - current_level_xp
    required_xp = next_level_xp - current_level_xp

    return {
        "level": level,
        "total_xp": total_xp,
        "current_level_xp": current_level_xp,
        "next_level_xp": next_level_xp,
        "progress_xp": progress_xp,
        "required_xp": required_xp,
    }


# --------------------------------------------------
# XP generation
# --------------------------------------------------

def generate_xp(xp_min: int, xp_max: int) -> int:
    """Generate a random XP amount within the configured range."""

    if xp_min < 1:
        raise ValueError("xp_min must be at least 1.")

    if xp_max < xp_min:
        raise ValueError("xp_max must be greater than or equal to xp_min.")

    return random.randint(xp_min, xp_max)


# --------------------------------------------------
# Guild leveling settings
# --------------------------------------------------

async def get_leveling_settings(pool, guild_id: int):
    """Get leveling settings for a guild."""

    guild = await repositories.get_guild(pool, guild_id)

    if guild is None:
        await repositories.create_guild(pool, guild_id)
        guild = await repositories.get_guild(pool, guild_id)

    return {
        "enabled": guild["leveling_enabled"],
        "xp_min": guild["xp_min"],
        "xp_max": guild["xp_max"],
        "level_up_messages_enabled": guild["level_up_messages_enabled"],
        "level_up_channel_id": guild["level_up_channel_id"],
    }


# --------------------------------------------------
# User leveling
# --------------------------------------------------

async def get_user_level(pool, user_id: int, guild_id: int):
    """Get a user's stored leveling data."""

    user = await repositories.get_user(
        pool,
        user_id,
        guild_id,
    )

    if user is None:
        await repositories.create_user(
            pool,
            user_id,
            guild_id,
        )

        user = await repositories.get_user(
            pool,
            user_id,
            guild_id,
        )

    return {
        "xp": user["xp"],
        "level": user["level"],
    }


def calculate_xp_update(
    current_xp: int,
    xp_amount: int,
) -> dict:
    """Calculate the result of adding XP without changing the database."""

    if xp_amount < 0:
        raise ValueError("xp_amount cannot be negative.")

    new_xp = current_xp + xp_amount

    old_level = calculate_level(current_xp)
    new_level = calculate_level(new_xp)

    return {
        "old_xp": current_xp,
        "new_xp": new_xp,
        "xp_added": xp_amount,
        "old_level": old_level,
        "new_level": new_level,
        "level_up": new_level > old_level,
        "levels_gained": new_level - old_level,
    }


async def add_xp(
    pool,
    user_id: int,
    guild_id: int,
    xp_amount: int,
) -> dict:
    """Add XP to a user and update their cached level."""

    user_data = await get_user_level(
        pool,
        user_id,
        guild_id,
    )

    result = calculate_xp_update(
        user_data["xp"],
        xp_amount,
    )

    await repositories.update_user_xp(
        pool,
        user_id,
        guild_id,
        result["new_xp"],
        result["new_level"],
    )

    progress = get_level_progress(
        result["new_xp"],
    )

    return {
        **result,
        **progress,
    }


async def award_message_xp(
    pool,
    user_id: int,
    guild_id: int,
) -> dict | None:
    """Award random XP for a valid message without lost concurrent updates."""

    async with _get_xp_lock(guild_id, user_id):
        if _is_on_xp_cooldown(guild_id, user_id, time.monotonic()):
            return None

        settings = await get_leveling_settings(
            pool,
            guild_id,
        )

        if not settings["enabled"]:
            return None

        xp_amount = generate_xp(
            settings["xp_min"],
            settings["xp_max"],
        )

        return await add_xp(
            pool,
            user_id,
            guild_id,
            xp_amount,
        )


# --------------------------------------------------
# Level rewards
# --------------------------------------------------

async def get_level_rewards(
    pool,
    guild_id: int,
    level: int,
):
    """Get all reward roles configured for a level."""

    return await repositories.get_level_rewards(
        pool,
        guild_id,
        level,
    )


async def get_all_level_rewards(
    pool,
    guild_id: int,
):
    """Get all level reward roles for a guild."""

    return await repositories.get_all_level_rewards(
        pool,
        guild_id,
    )


async def add_level_reward(
    pool,
    guild_id: int,
    level: int,
    role_id: int,
):
    """Add a reward role to a level."""

    return await repositories.add_level_reward(
        pool,
        guild_id,
        level,
        role_id,
    )


async def remove_level_reward(
    pool,
    guild_id: int,
    level: int,
    role_id: int,
):
    """Remove a reward role from a level."""

    return await repositories.remove_level_reward(
        pool,
        guild_id,
        level,
        role_id,
    )


# --------------------------------------------------
# Level-up rewards and announcements
# --------------------------------------------------

async def get_level_up_data(
    pool,
    guild_id: int,
    old_level: int,
    new_level: int,
) -> dict:
    """Return reward and announcement data for a level-up."""

    if new_level <= old_level:
        return {
            "level_up": False,
            "levels": [],
            "reward_roles": [],
            "announcement": {
                "enabled": False,
                "channel_id": None,
            },
        }

    crossed_levels = list(
        range(
            old_level + 1,
            new_level + 1,
        )
    )

    reward_roles = []

    for level in crossed_levels:
        rewards = await get_level_rewards(
            pool,
            guild_id,
            level,
        )

        for reward in rewards:
            reward_roles.append(
                {
                    "level": level,
                    "role_id": reward["role_id"],
                }
            )

    settings = await get_leveling_settings(
        pool,
        guild_id,
    )

    return {
        "level_up": True,
        "levels": crossed_levels,
        "reward_roles": reward_roles,
        "announcement": {
            "enabled": settings["level_up_messages_enabled"],
            "channel_id": settings["level_up_channel_id"],
        },
    }


