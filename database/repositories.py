# =========================
# User Repository
# =========================


async def get_user(
    pool,
    user_id: int,
    guild_id: int,
):
    """Get a user's data from a specific server."""

    query = """
    SELECT *
    FROM users
    WHERE user_id = $1
      AND guild_id = $2
    """

    return await pool.fetchrow(
        query,
        user_id,
        guild_id,
    )


async def create_user(
    pool,
    user_id: int,
    guild_id: int,
):
    """Create a user record for a specific server."""

    query = """
    INSERT INTO users (
        user_id,
        guild_id
    )
    VALUES ($1, $2)
    ON CONFLICT (user_id, guild_id)
    DO NOTHING
    """

    await pool.execute(
        query,
        user_id,
        guild_id,
    )


async def update_user_xp(
    pool,
    user_id: int,
    guild_id: int,
    xp: int,
    level: int,
):
    """Update a user's XP and level."""

    query = """
    UPDATE users
    SET xp = $1,
        level = $2
    WHERE user_id = $3
      AND guild_id = $4
    """

    await pool.execute(
        query,
        xp,
        level,
        user_id,
        guild_id,
    )


async def increment_message_count(
    pool,
    user_id: int,
    guild_id: int,
):
    """Increase a user's total message count by one."""

    query = """
    UPDATE users
    SET message_count = message_count + 1
    WHERE user_id = $1
      AND guild_id = $2
    """

    await pool.execute(
        query,
        user_id,
        guild_id,
    )


async def increment_voice_seconds(
    pool,
    user_id: int,
    guild_id: int,
    seconds: int,
):
    """Increase a user's total voice time."""

    if seconds <= 0:
        return

    query = """
    UPDATE users
    SET voice_seconds = voice_seconds + $1
    WHERE user_id = $2
      AND guild_id = $3
    """

    await pool.execute(
        query,
        seconds,
        user_id,
        guild_id,
    )


async def get_level_stats(
    pool,
    guild_id: int,
):
    """Get current level statistics for users."""
    query = """
    SELECT
        user_id,
        level,
        xp
    FROM users
    WHERE guild_id = $1
    ORDER BY level DESC, xp DESC, user_id ASC
    """

    return await pool.fetch(
        query,
        guild_id,
    )




# =========================
# Guild Repository
# =========================


async def get_guild(
    pool,
    guild_id: int,
):
    """Get configuration for a specific server."""

    query = """
    SELECT *
    FROM guilds
    WHERE guild_id = $1
    """

    return await pool.fetchrow(
        query,
        guild_id,
    )


async def create_guild(
    pool,
    guild_id: int,
):
    """Create a server configuration record."""

    query = """
    INSERT INTO guilds (
        guild_id
    )
    VALUES ($1)
    ON CONFLICT (guild_id)
    DO NOTHING
    """

    await pool.execute(
        query,
        guild_id,
    )


async def update_guild_setting(
    pool,
    guild_id: int,
    setting: str,
    value,
):
    """Update a single server setting."""

    allowed_settings = {
        "message_tracking_enabled",
        "voice_tracking_enabled",

        "spam_enabled",
        "link_protection_enabled",

        "spam_message_limit",
        "spam_message_window",
        "emoji_spam_limit",

        "spam_action",
        "spam_timeout_seconds",
        "emoji_spam_action",
        "emoji_spam_timeout_seconds",
        "link_action",
        "link_timeout_seconds",

        "leveling_enabled",
        "xp_min",
        "xp_max",

        "level_up_messages_enabled",
        "level_up_channel_id",
        "announcement_channel_id",
        "welcome_enabled",
        "welcome_channel_id",
        "welcome_message",
        "welcome_gif_url",
        "leave_enabled",
        "leave_channel_id",
        "leave_message",
        "leave_gif_url",
        "level_up_message",
        "level_up_gif_url",
        "verification_enabled",
        "verification_channel_id",
        "verification_role_id",
    }

    if setting not in allowed_settings:
        raise ValueError(
            f"Invalid guild setting: {setting}"
        )

    # =========================
    # Validate Moderation Actions
    # =========================

    action_settings = {
        "spam_action",
        "emoji_spam_action",
        "link_action",
    }

    if setting in action_settings:
        allowed_actions = {
            "warn",
            "delete",
            "timeout",
        }

        if value not in allowed_actions:
            raise ValueError(
                f"Invalid action: {value}"
            )

    # =========================
    # Validate Numeric Settings
    # =========================

    numeric_settings = {
        "spam_message_limit",
        "spam_message_window",
        "emoji_spam_limit",
        "spam_timeout_seconds",
        "emoji_spam_timeout_seconds",
        "xp_min",
        "xp_max",
        "link_timeout_seconds",
    }

    if setting in numeric_settings:
        if not isinstance(value, int):
            raise ValueError(
                f"{setting} must be an integer."
            )

        if value < 1:
            raise ValueError(
                f"{setting} must be greater than zero."
            )

    # =========================
    # XP Range Validation
    # =========================

    if setting == "xp_min" or setting == "xp_max":
        current_guild = await get_guild(
            pool,
            guild_id,
        )

        if current_guild is None:
            raise ValueError(
                "Guild configuration does not exist."
            )

        current_xp_min = current_guild["xp_min"]
        current_xp_max = current_guild["xp_max"]

        if setting == "xp_min":
            if value > current_xp_max:
                raise ValueError(
                    "xp_min cannot be greater than xp_max."
                )

        if setting == "xp_max":
            if value < current_xp_min:
                raise ValueError(
                    "xp_max cannot be less than xp_min."
                )

    query = f"""
    UPDATE guilds
    SET {setting} = $1
    WHERE guild_id = $2
    """

    result = await pool.execute(
        query,
        value,
        guild_id,
    )

    return result





# =========================
# Channel Rules Repository
# =========================


async def get_channel_rules(
    pool,
    guild_id: int,
    channel_id: int,
):
    """Get restriction rules for a specific channel."""

    query = """
    SELECT *
    FROM channel_rules
    WHERE guild_id = $1
      AND channel_id = $2
    """

    return await pool.fetchrow(
        query,
        guild_id,
        channel_id,
    )


async def create_channel_rules(
    pool,
    guild_id: int,
    channel_id: int,
):
    """Create default rules for a channel."""

    query = """
    INSERT INTO channel_rules (
        guild_id,
        channel_id
    )
    VALUES ($1, $2)
    ON CONFLICT (guild_id, channel_id)
    DO NOTHING
    """

    await pool.execute(
        query,
        guild_id,
        channel_id,
    )


async def update_channel_rule(
    pool,
    guild_id: int,
    channel_id: int,
    rule: str,
    enabled: bool,
):
    """Enable or disable a specific channel restriction."""

    allowed_rules = {
        "image_only",
        "clips_only",
    }

    if rule not in allowed_rules:
        raise ValueError(
            f"Invalid channel rule: {rule}"
        )

    await create_channel_rules(
        pool,
        guild_id,
        channel_id,
    )

    query = f"""
    UPDATE channel_rules
    SET {rule} = $1
    WHERE guild_id = $2
      AND channel_id = $3
    """

    await pool.execute(
        query,
        enabled,
        guild_id,
        channel_id,
    )





# =========================
# Statistics Excluded Channels Repository
# =========================


async def add_statistics_excluded_channel(
    pool,
    guild_id: int,
    channel_id: int,
):
    """Exclude a channel from statistics."""

    query = """
    INSERT INTO statistics_excluded_channels (
        guild_id,
        channel_id
    )
    VALUES ($1, $2)
    ON CONFLICT (
        guild_id,
        channel_id
    )
    DO NOTHING
    """

    await pool.execute(
        query,
        guild_id,
        channel_id,
    )


async def remove_statistics_excluded_channel(
    pool,
    guild_id: int,
    channel_id: int,
):
    """Remove a channel from the statistics exclusion list."""

    query = """
    DELETE FROM statistics_excluded_channels
    WHERE guild_id = $1
      AND channel_id = $2
    """

    await pool.execute(
        query,
        guild_id,
        channel_id,
    )


async def is_statistics_channel_excluded(
    pool,
    guild_id: int,
    channel_id: int,
):
    """Check whether a channel is excluded from statistics."""

    query = """
    SELECT 1
    FROM statistics_excluded_channels
    WHERE guild_id = $1
      AND channel_id = $2
    """

    result = await pool.fetchval(
        query,
        guild_id,
        channel_id,
    )

    return result is not None


async def get_statistics_excluded_channels(
    pool,
    guild_id: int,
):
    """Get all channels excluded from statistics."""

    query = """
    SELECT channel_id
    FROM statistics_excluded_channels
    WHERE guild_id = $1
    ORDER BY channel_id
    """

    return await pool.fetch(
        query,
        guild_id,
    )





# =========================
# Whitelist Repository
# =========================


async def add_whitelist(
    pool,
    guild_id: int,
    target_id: int,
    restriction_type: str,
):
    """Whitelist a user or role for a specific restriction."""

    allowed_restrictions = {
        "image_only",
        "clips_only",
    }

    if restriction_type not in allowed_restrictions:
        raise ValueError(
            f"Invalid restriction type: {restriction_type}"
        )

    query = """
    INSERT INTO whitelists (
        guild_id,
        target_id,
        restriction_type
    )
    VALUES ($1, $2, $3)
    ON CONFLICT (
        guild_id,
        target_id,
        restriction_type
    )
    DO NOTHING
    """

    await pool.execute(
        query,
        guild_id,
        target_id,
        restriction_type,
    )


async def remove_whitelist(
    pool,
    guild_id: int,
    target_id: int,
    restriction_type: str,
):
    """Remove a user or role from a restriction whitelist."""

    allowed_restrictions = {
        "image_only",
        "clips_only",
    }

    if restriction_type not in allowed_restrictions:
        raise ValueError(
            f"Invalid restriction type: {restriction_type}"
        )

    query = """
    DELETE FROM whitelists
    WHERE guild_id = $1
      AND target_id = $2
      AND restriction_type = $3
    """

    await pool.execute(
        query,
        guild_id,
        target_id,
        restriction_type,
    )


async def is_whitelisted(
    pool,
    guild_id: int,
    target_id: int,
    restriction_type: str,
):
    """Check whether a user or role is whitelisted."""

    allowed_restrictions = {
        "image_only",
        "clips_only",
    }

    if restriction_type not in allowed_restrictions:
        raise ValueError(
            f"Invalid restriction type: {restriction_type}"
        )

    query = """
    SELECT 1
    FROM whitelists
    WHERE guild_id = $1
      AND target_id = $2
      AND restriction_type = $3
    """

    result = await pool.fetchval(
        query,
        guild_id,
        target_id,
        restriction_type,
    )

    return result is not None





# =========================
# AFK Repository
# =========================


async def get_afk_user(
    pool,
    guild_id: int,
    user_id: int,
):
    """Get a user's AFK record from a specific server."""

    query = """
    SELECT *
    FROM afk_users
    WHERE guild_id = $1
      AND user_id = $2
    """

    return await pool.fetchrow(
        query,
        guild_id,
        user_id,
    )


async def set_afk(
    pool,
    guild_id: int,
    user_id: int,
    reason: str | None = None,
):
    """Set or update a user's AFK status."""

    query = """
    INSERT INTO afk_users (
        guild_id,
        user_id,
        reason
    )
    VALUES ($1, $2, $3)
    ON CONFLICT (guild_id, user_id)
    DO UPDATE SET
        reason = EXCLUDED.reason,
        started_at = NOW()
    """

    await pool.execute(
        query,
        guild_id,
        user_id,
        reason,
    )


async def remove_afk(
    pool,
    guild_id: int,
    user_id: int,
):
    """Remove a user's AFK status."""

    query = """
    DELETE FROM afk_users
    WHERE guild_id = $1
      AND user_id = $2
    """

    await pool.execute(
        query,
        guild_id,
        user_id,
    )





# =========================
# Invite Tracking Repository
# =========================


async def get_inviter(
    pool,
    guild_id: int,
    user_id: int,
):
    """Get the tracked inviter of a user."""

    query = """
    SELECT inviter_id
    FROM invite_tracking
    WHERE guild_id = $1
      AND user_id = $2
    """

    return await pool.fetchval(
        query,
        guild_id,
        user_id,
    )


async def set_inviter(
    pool,
    guild_id: int,
    user_id: int,
    inviter_id: int | None,
):
    """Store or update the inviter of a user."""

    query = """
    INSERT INTO invite_tracking (
        guild_id,
        user_id,
        inviter_id
    )
    VALUES ($1, $2, $3)
    ON CONFLICT (guild_id, user_id)
    DO UPDATE SET
        inviter_id = EXCLUDED.inviter_id
    """

    await pool.execute(
        query,
        guild_id,
        user_id,
        inviter_id,
    )





# =========================
# Level Rewards Repository
# =========================


async def get_level_rewards(
    pool,
    guild_id: int,
    level: int,
):
    """Get all reward roles configured for a specific level."""

    query = """
    SELECT role_id
    FROM level_rewards
    WHERE guild_id = $1
      AND level = $2
    ORDER BY role_id
    """

    return await pool.fetch(
        query,
        guild_id,
        level,
    )


async def add_level_reward(
    pool,
    guild_id: int,
    level: int,
    role_id: int,
):
    """Add a role reward for a specific level."""

    if level < 1:
        raise ValueError(
            "Level must be greater than or equal to 1."
        )

    query = """
    INSERT INTO level_rewards (
        guild_id,
        level,
        role_id
    )
    VALUES ($1, $2, $3)
    ON CONFLICT (
        guild_id,
        level,
        role_id
    )
    DO NOTHING
    """

    await pool.execute(
        query,
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
    """Remove a role reward from a specific level."""

    query = """
    DELETE FROM level_rewards
    WHERE guild_id = $1
      AND level = $2
      AND role_id = $3
    """

    await pool.execute(
        query,
        guild_id,
        level,
        role_id,
    )


async def get_all_level_rewards(
    pool,
    guild_id: int,
):
    """Get all configured level rewards for a server."""

    query = """
    SELECT level, role_id
    FROM level_rewards
    WHERE guild_id = $1
    ORDER BY level ASC, role_id ASC
    """

    return await pool.fetch(
        query,
        guild_id,
    )





# =========================
# Weekly Leaderboard Rewards Repository
# =========================


async def get_leaderboard_reward_role(
    pool,
    guild_id: int,
    leaderboard_type: str,
):
    """Get the configured weekly reward role for a leaderboard."""

    allowed_types = {
        "messages",
        "voice",
    }

    if leaderboard_type not in allowed_types:
        raise ValueError(
            f"Invalid leaderboard type: {leaderboard_type}"
        )

    query = """
    SELECT role_id
    FROM leaderboard_rewards
    WHERE guild_id = $1
      AND leaderboard_type = $2
    """

    return await pool.fetchval(
        query,
        guild_id,
        leaderboard_type,
    )


async def set_leaderboard_reward_role(
    pool,
    guild_id: int,
    leaderboard_type: str,
    role_id: int,
):
    """Set the weekly reward role for a leaderboard."""

    allowed_types = {
        "messages",
        "voice",
    }

    if leaderboard_type not in allowed_types:
        raise ValueError(
            f"Invalid leaderboard type: {leaderboard_type}"
        )

    query = """
    INSERT INTO leaderboard_rewards (
        guild_id,
        leaderboard_type,
        role_id
    )
    VALUES ($1, $2, $3)
    ON CONFLICT (guild_id, leaderboard_type)
    DO UPDATE SET
        role_id = EXCLUDED.role_id
    """

    await pool.execute(
        query,
        guild_id,
        leaderboard_type,
        role_id,
    )


async def remove_leaderboard_reward_role(
    pool,
    guild_id: int,
    leaderboard_type: str,
):
    """Remove the configured weekly leaderboard reward role."""

    allowed_types = {
        "messages",
        "voice",
    }

    if leaderboard_type not in allowed_types:
        raise ValueError(
            f"Invalid leaderboard type: {leaderboard_type}"
        )

    query = """
    DELETE FROM leaderboard_rewards
    WHERE guild_id = $1
      AND leaderboard_type = $2
    """

    await pool.execute(
        query,
        guild_id,
        leaderboard_type,
    )



# =========================
# Message Recovery Repository
# =========================


async def get_message_recovery_state(
    pool,
    guild_id: int,
    channel_id: int,
):
    """Get the last message recovery checkpoint for a channel."""

    query = """
    SELECT last_scanned_at
    FROM message_recovery_state
    WHERE guild_id = $1
      AND channel_id = $2
    """

    return await pool.fetchval(
        query,
        guild_id,
        channel_id,
    )


async def set_message_recovery_state(
    pool,
    guild_id: int,
    channel_id: int,
    last_scanned_at,
):
    """Save the last successful message recovery checkpoint."""

    query = """
    INSERT INTO message_recovery_state (
        guild_id,
        channel_id,
        last_scanned_at
    )
    VALUES ($1, $2, $3)
    ON CONFLICT (guild_id, channel_id)
    DO UPDATE SET
        last_scanned_at = EXCLUDED.last_scanned_at
    """

    await pool.execute(
        query,
        guild_id,
        channel_id,
        last_scanned_at,
    )


# =========================
# Recovery Requests Repository
# =========================
#
# Backs the dashboard's on-demand "Rescan" action (see
# dashboard/backend/api/routes/recovery.py). The dashboard only ever
# inserts/reads here; RECOVERY_REQUEST_POLL_LOOP in bot/events.py is the
# only thing that deletes a row, once it has actually rescanned the
# channel.


async def create_recovery_request(pool, guild_id: int, channel_id: int, requested_by: int | None = None):
    """Queue an on-demand rescan for a channel. Safe to call again for a
    channel that already has a pending request — it just refreshes the
    timestamp instead of creating a duplicate."""

    query = """
    INSERT INTO recovery_requests (guild_id, channel_id, requested_by)
    VALUES ($1, $2, $3)
    ON CONFLICT (guild_id, channel_id)
    DO UPDATE SET
        requested_at = NOW(),
        requested_by = EXCLUDED.requested_by
    """

    await pool.execute(query, guild_id, channel_id, requested_by)


async def list_pending_recovery_requests(pool):
    """Every rescan request waiting to be processed, across all guilds."""

    query = "SELECT guild_id, channel_id, requested_at, requested_by FROM recovery_requests"
    return await pool.fetch(query)


async def get_recovery_request(pool, guild_id: int, channel_id: int):
    """Check whether a channel currently has a pending rescan request —
    used by the dashboard to show a "pending" state on the Recovery
    page."""

    query = """
    SELECT requested_at
    FROM recovery_requests
    WHERE guild_id = $1 AND channel_id = $2
    """
    return await pool.fetchval(query, guild_id, channel_id)


async def delete_recovery_request(pool, guild_id: int, channel_id: int):
    """Clear a rescan request once it's been processed."""

    query = "DELETE FROM recovery_requests WHERE guild_id = $1 AND channel_id = $2"
    await pool.execute(query, guild_id, channel_id)


async def claim_processed_message(
    connection,
    guild_id: int,
    message_id: int,
    channel_id: int,
    user_id: int,
    message_created_at,
):
    """Claim a message for statistics processing exactly once."""

    query = """
    INSERT INTO processed_messages (
        guild_id,
        message_id,
        channel_id,
        user_id,
        message_created_at
    )
    VALUES ($1, $2, $3, $4, $5)
    ON CONFLICT (guild_id, message_id)
    DO NOTHING
    RETURNING message_id
    """

    result = await connection.fetchval(
        query,
        guild_id,
        message_id,
        channel_id,
        user_id,
        message_created_at,
    )

    return result is not None


async def record_message_statistics_once(
    pool,
    guild_id: int,
    user_id: int,
    channel_id: int,
    statistic_date,
    message_id: int,
    message_created_at,
):
    """Record message statistics exactly once in one transaction."""

    async with pool.acquire() as connection:
        async with connection.transaction():

            # Make sure the user exists.
            await connection.execute(
                """
                INSERT INTO users (
                    user_id,
                    guild_id
                )
                VALUES ($1, $2)
                ON CONFLICT (user_id, guild_id)
                DO NOTHING
                """,
                user_id,
                guild_id,
            )

            # Claim the message.
            claimed = await claim_processed_message(
                connection,
                guild_id,
                message_id,
                channel_id,
                user_id,
                message_created_at,
            )

            # Already processed.
            if not claimed:
                return False

            # =========================
            # User All-Time Statistics
            # =========================

            await connection.execute(
                """
                UPDATE users
                SET message_count = message_count + 1
                WHERE user_id = $1
                  AND guild_id = $2
                """,
                user_id,
                guild_id,
            )

            # =========================
            # User Daily Statistics
            # =========================

            await connection.execute(
                """
                INSERT INTO message_statistics (
                    guild_id,
                    user_id,
                    statistic_date,
                    message_count
                )
                VALUES ($1, $2, $3, 1)
                ON CONFLICT (
                    guild_id,
                    user_id,
                    statistic_date
                )
                DO UPDATE SET
                    message_count =
                        message_statistics.message_count + 1
                """,
                guild_id,
                user_id,
                statistic_date,
            )

            # =========================
            # Channel Daily Statistics
            # =========================

            await connection.execute(
                """
                INSERT INTO channel_message_statistics (
                    guild_id,
                    channel_id,
                    statistic_date,
                    message_count
                )
                VALUES ($1, $2, $3, 1)
                ON CONFLICT (
                    guild_id,
                    channel_id,
                    statistic_date
                )
                DO UPDATE SET
                    message_count =
                        channel_message_statistics.message_count + 1
                """,
                guild_id,
                channel_id,
                statistic_date,
            )

            return True



# =========================
# Message Statistics Repository
# =========================


async def increment_daily_message_stat(
    pool,
    guild_id: int,
    user_id: int,
    statistic_date,
    amount: int = 1,
):
    """Increase a user's message count for a specific day."""

    if amount <= 0:
        return

    query = """
    INSERT INTO message_statistics (
        guild_id,
        user_id,
        statistic_date,
        message_count
    )
    VALUES ($1, $2, $3, $4)
    ON CONFLICT (
        guild_id,
        user_id,
        statistic_date
    )
    DO UPDATE SET
        message_count =
            message_statistics.message_count
            + EXCLUDED.message_count
    """

    await pool.execute(
        query,
        guild_id,
        user_id,
        statistic_date,
        amount,
    )


async def get_daily_message_stats(
    pool,
    guild_id: int,
    start_date,
    end_date,
):
    """Get user message statistics for a date range."""

    query = """
    SELECT
        user_id,
        SUM(message_count) AS message_count
    FROM message_statistics
    WHERE guild_id = $1
      AND statistic_date >= $2
      AND statistic_date < $3
    GROUP BY user_id
    ORDER BY message_count DESC, user_id ASC
    """

    return await pool.fetch(
        query,
        guild_id,
        start_date,
        end_date,
    )

async def get_all_message_stats(
    pool,
    guild_id: int,
):
    """Get all-time message statistics for users."""
    query = """
    SELECT
        user_id,
        message_count
    FROM users
    WHERE guild_id = $1
      AND message_count > 0
    ORDER BY message_count DESC, user_id ASC
    """

    return await pool.fetch(
        query,
        guild_id,
    )



# =========================
# Voice Statistics Repository
# =========================


async def increment_daily_voice_stat(
    pool,
    guild_id: int,
    user_id: int,
    statistic_date,
    seconds: int,
):
    """Increase a user's voice time for a specific day."""

    if seconds <= 0:
        return

    query = """
    INSERT INTO voice_statistics (
        guild_id,
        user_id,
        statistic_date,
        voice_seconds
    )
    VALUES ($1, $2, $3, $4)
    ON CONFLICT (
        guild_id,
        user_id,
        statistic_date
    )
    DO UPDATE SET
        voice_seconds =
            voice_statistics.voice_seconds
            + EXCLUDED.voice_seconds
    """

    await pool.execute(
        query,
        guild_id,
        user_id,
        statistic_date,
        seconds,
    )


async def get_daily_voice_stats(
    pool,
    guild_id: int,
    start_date,
    end_date,
):
    """Get user voice statistics for a date range."""

    query = """
    SELECT
        user_id,
        SUM(voice_seconds) AS voice_seconds
    FROM voice_statistics
    WHERE guild_id = $1
      AND statistic_date >= $2
      AND statistic_date < $3
    GROUP BY user_id
    ORDER BY voice_seconds DESC, user_id ASC
    """

    return await pool.fetch(
        query,
        guild_id,
        start_date,
        end_date,
    )


async def get_all_voice_stats(
    pool,
    guild_id: int,
):
    """Get all-time voice statistics for users."""
    query = """
    SELECT
        user_id,
        voice_seconds
    FROM users
    WHERE guild_id = $1
      AND voice_seconds > 0
    ORDER BY voice_seconds DESC, user_id ASC
    """

    return await pool.fetch(
        query,
        guild_id,
    )



# =========================
# Channel Message Statistics
# =========================


async def increment_daily_channel_message_stat(
    pool,
    guild_id: int,
    channel_id: int,
    statistic_date,
    amount: int = 1,
):
    """Increase message usage for a channel on a specific day."""

    if amount <= 0:
        return

    query = """
    INSERT INTO channel_message_statistics (
        guild_id,
        channel_id,
        statistic_date,
        message_count
    )
    VALUES ($1, $2, $3, $4)
    ON CONFLICT (
        guild_id,
        channel_id,
        statistic_date
    )
    DO UPDATE SET
        message_count =
            channel_message_statistics.message_count
            + EXCLUDED.message_count
    """

    await pool.execute(
        query,
        guild_id,
        channel_id,
        statistic_date,
        amount,
    )


async def get_daily_channel_message_stats(
    pool,
    guild_id: int,
    start_date,
    end_date,
):
    """Get channel message usage for a date range."""

    query = """
    SELECT
        channel_id,
        SUM(message_count) AS message_count
    FROM channel_message_statistics
    WHERE guild_id = $1
      AND statistic_date >= $2
      AND statistic_date < $3
    GROUP BY channel_id
    ORDER BY message_count DESC, channel_id ASC
    """

    return await pool.fetch(
        query,
        guild_id,
        start_date,
        end_date,
    )


async def get_all_channel_message_stats(
    pool,
    guild_id: int,
):
    """Get all-time message statistics for channels."""
    query = """
    SELECT
        channel_id,
        SUM(message_count) AS message_count
    FROM channel_message_statistics
    WHERE guild_id = $1
    GROUP BY channel_id
    ORDER BY message_count DESC, channel_id ASC
    """

    return await pool.fetch(
        query,
        guild_id,
    )




# =========================
# Channel Voice Statistics
# =========================


async def increment_daily_channel_voice_stat(
    pool,
    guild_id: int,
    channel_id: int,
    statistic_date,
    seconds: int,
):
    """Increase voice usage for a channel on a specific day."""

    if seconds <= 0:
        return

    query = """
    INSERT INTO channel_voice_statistics (
        guild_id,
        channel_id,
        statistic_date,
        voice_seconds
    )
    VALUES ($1, $2, $3, $4)
    ON CONFLICT (
        guild_id,
        channel_id,
        statistic_date
    )
    DO UPDATE SET
        voice_seconds =
            channel_voice_statistics.voice_seconds
            + EXCLUDED.voice_seconds
    """

    await pool.execute(
        query,
        guild_id,
        channel_id,
        statistic_date,
        seconds,
    )


async def get_daily_channel_voice_stats(
    pool,
    guild_id: int,
    start_date,
    end_date,
):
    """Get channel voice usage for a date range."""

    query = """
    SELECT
        channel_id,
        SUM(voice_seconds) AS voice_seconds
    FROM channel_voice_statistics
    WHERE guild_id = $1
      AND statistic_date >= $2
      AND statistic_date < $3
    GROUP BY channel_id
    ORDER BY voice_seconds DESC, channel_id ASC
    """

    return await pool.fetch(
        query,
        guild_id,
        start_date,
        end_date,
    )


async def get_all_channel_voice_stats(
    pool,
    guild_id: int,
):
    """Get all-time voice statistics for channels."""
    query = """
    SELECT
        channel_id,
        SUM(voice_seconds) AS voice_seconds
    FROM channel_voice_statistics
    WHERE guild_id = $1
    GROUP BY channel_id
    ORDER BY voice_seconds DESC, channel_id ASC
    """

    return await pool.fetch(
        query,
        guild_id,
    )



# =========================
# Voice Time Recording
# =========================


async def add_voice_time(
    pool,
    user_id: int,
    guild_id: int,
    channel_id: int,
    statistic_date,
    seconds: int,
):
    """Add counted voice time to user and channel statistics."""

    if seconds <= 0:
        return

    # User's all-time voice time
    await increment_voice_seconds(
        pool,
        user_id,
        guild_id,
        seconds,
    )

    # User's daily voice time
    await increment_daily_voice_stat(
        pool,
        guild_id,
        user_id,
        statistic_date,
        seconds,
    )

    # Channel's daily voice usage
    await increment_daily_channel_voice_stat(
        pool,
        guild_id,
        channel_id,
        statistic_date,
        seconds,
    )





# =========================
# Warning Repository
# =========================


async def get_warning_count(
    pool,
    user_id: int,
    guild_id: int,
):
    """Get the total warning count for a user in a server."""

    query = """
    SELECT warnings
    FROM users
    WHERE user_id = $1
      AND guild_id = $2
    """

    result = await pool.fetchval(
        query,
        user_id,
        guild_id,
    )

    return result or 0


async def increment_warning_count(
    pool,
    user_id: int,
    guild_id: int,
):
    """Increase a user's warning count by one."""

    query = """
    UPDATE users
    SET warnings = warnings + 1
    WHERE user_id = $1
      AND guild_id = $2
    """

    await pool.execute(
        query,
        user_id,
        guild_id,
    )


async def decrement_warning_count(
    pool,
    user_id: int,
    guild_id: int,
):
    """Decrease a user's warning count by one without going below zero."""

    query = """
    UPDATE users
    SET warnings = GREATEST(warnings - 1, 0)
    WHERE user_id = $1
      AND guild_id = $2
    """

    await pool.execute(
        query,
        user_id,
        guild_id,
    )


async def clear_warning_count(
    pool,
    user_id: int,
    guild_id: int,
):
    """Clear all warnings for a user in a server."""

    query = """
    UPDATE users
    SET warnings = 0
    WHERE user_id = $1
      AND guild_id = $2
    """

    await pool.execute(
        query,
        user_id,
        guild_id,
    )





# =========================
# Warning History Repository
# =========================


async def add_warning(
    pool,
    guild_id: int,
    user_id: int,
    moderator_id: int,
    reason: str | None = None,
):
    """Add a warning to a user and store its history."""

    query = """
    INSERT INTO warning_history (
        guild_id,
        user_id,
        moderator_id,
        reason
    )
    VALUES ($1, $2, $3, $4)
    RETURNING warning_id
    """

    warning_id = await pool.fetchval(
        query,
        guild_id,
        user_id,
        moderator_id,
        reason,
    )

    await increment_warning_count(
        pool,
        user_id,
        guild_id,
    )

    return warning_id



async def add_spam_warning(
    pool,
    guild_id: int,
    user_id: int,
    reason: str = "Spam detected",
):
    """Add an automatic warning caused by spam detection."""

    return await add_warning(
        pool,
        guild_id,
        user_id,
        0,
        reason,
    )



async def get_warning_history(
    pool,
    guild_id: int,
    user_id: int,
):
    """Get warning history for a user."""

    query = """
    SELECT
        warning_id,
        moderator_id,
        reason,
        created_at
    FROM warning_history
    WHERE guild_id = $1
      AND user_id = $2
    ORDER BY created_at DESC, warning_id DESC
    """

    return await pool.fetch(
        query,
        guild_id,
        user_id,
    )


async def get_warning(
    pool,
    guild_id: int,
    warning_id: int,
):
    """Get a specific warning by its ID."""

    query = """
    SELECT
        warning_id,
        user_id,
        moderator_id,
        reason,
        created_at
    FROM warning_history
    WHERE guild_id = $1
      AND warning_id = $2
    """

    return await pool.fetchrow(
        query,
        guild_id,
        warning_id,
    )


async def remove_warning(
    pool,
    guild_id: int,
    warning_id: int,
):
    """Remove a specific warning and update the warning count."""

    query = """
    DELETE FROM warning_history
    WHERE guild_id = $1
      AND warning_id = $2
    RETURNING user_id
    """

    user_id = await pool.fetchval(
        query,
        guild_id,
        warning_id,
    )

    if user_id is None:
        return False

    await decrement_warning_count(
        pool,
        user_id,
        guild_id,
    )

    return True


async def clear_warning_history(
    pool,
    guild_id: int,
    user_id: int,
):
    """Remove all warning history for a user."""

    query = """
    DELETE FROM warning_history
    WHERE guild_id = $1
      AND user_id = $2
    """

    await pool.execute(
        query,
        guild_id,
        user_id,
    )

    await clear_warning_count(
        pool,
        user_id,
        guild_id,
    )










