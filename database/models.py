# =========================
# Database Table Definitions
# =========================


# =========================
# Users
# =========================

USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,

    xp BIGINT NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 0,

    message_count BIGINT NOT NULL DEFAULT 0,
    voice_seconds BIGINT NOT NULL DEFAULT 0,

    warnings INTEGER NOT NULL DEFAULT 0,

    PRIMARY KEY (user_id, guild_id)
);
"""


# =========================
# Guild Configuration
# =========================

GUILDS_TABLE = """
CREATE TABLE IF NOT EXISTS guilds (
    guild_id BIGINT PRIMARY KEY,

    message_tracking_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    voice_tracking_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    spam_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    link_protection_enabled BOOLEAN NOT NULL DEFAULT FALSE,

    spam_message_limit INTEGER NOT NULL DEFAULT 5,
    spam_message_window INTEGER NOT NULL DEFAULT 5,

    emoji_spam_limit INTEGER NOT NULL DEFAULT 5,

    spam_action TEXT NOT NULL DEFAULT 'warn',
    spam_timeout_seconds INTEGER NOT NULL DEFAULT 60,

    emoji_spam_action TEXT NOT NULL DEFAULT 'warn',
    emoji_spam_timeout_seconds INTEGER NOT NULL DEFAULT 60,

    link_action TEXT NOT NULL DEFAULT 'delete',
    link_timeout_seconds INTEGER NOT NULL DEFAULT 60,

    leveling_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    xp_min INTEGER NOT NULL DEFAULT 5,
    xp_max INTEGER NOT NULL DEFAULT 10,

    level_up_messages_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    level_up_channel_id BIGINT,
    announcement_channel_id BIGINT,

    welcome_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    welcome_channel_id BIGINT,
    welcome_message TEXT NOT NULL DEFAULT 'Welcome {user} to {server}! 🎉',
    welcome_gif_url TEXT,

    leave_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    leave_channel_id BIGINT,
    leave_message TEXT NOT NULL DEFAULT '{username} has left {server}. 👋',
    leave_gif_url TEXT,

    level_up_message TEXT NOT NULL DEFAULT '{user} reached **Level {level}**! 🎉',
    level_up_gif_url TEXT,

    verification_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    verification_channel_id BIGINT,
    verification_role_id BIGINT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


# =========================
# Channel Rules
# =========================

CHANNEL_RULES_TABLE = """
CREATE TABLE IF NOT EXISTS channel_rules (
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,

    image_only BOOLEAN NOT NULL DEFAULT FALSE,
    clips_only BOOLEAN NOT NULL DEFAULT FALSE,

    PRIMARY KEY (guild_id, channel_id)
);
"""


# =========================
# Statistics Excluded Channels
# =========================

STATISTICS_EXCLUDED_CHANNELS_TABLE = """
CREATE TABLE IF NOT EXISTS statistics_excluded_channels (
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,

    PRIMARY KEY (guild_id, channel_id)
);
"""


# =========================
# Restriction Whitelists
# =========================

WHITELISTS_TABLE = """
CREATE TABLE IF NOT EXISTS whitelists (
    guild_id BIGINT NOT NULL,
    target_id BIGINT NOT NULL,

    restriction_type TEXT NOT NULL,

    PRIMARY KEY (guild_id, target_id, restriction_type)
);
"""


# =========================
# AFK Users
# =========================

AFK_TABLE = """
CREATE TABLE IF NOT EXISTS afk_users (
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,

    reason TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (guild_id, user_id)
);
"""


# =========================
# Invite Tracking
# =========================

INVITES_TABLE = """
CREATE TABLE IF NOT EXISTS invite_tracking (
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,

    inviter_id BIGINT,

    PRIMARY KEY (guild_id, user_id)
);
"""


# =========================
# Level Rewards
# =========================

LEVEL_REWARDS_TABLE = """
CREATE TABLE IF NOT EXISTS level_rewards (
    guild_id BIGINT NOT NULL,
    level INTEGER NOT NULL,
    role_id BIGINT NOT NULL,

    PRIMARY KEY (guild_id, level, role_id)
);
"""


# =========================
# Weekly Leaderboard Rewards
# =========================

LEADERBOARD_REWARDS_TABLE = """
CREATE TABLE IF NOT EXISTS leaderboard_rewards (
    guild_id BIGINT NOT NULL,
    leaderboard_type TEXT NOT NULL,
    role_id BIGINT NOT NULL,

    PRIMARY KEY (guild_id, leaderboard_type)
);
"""


# =========================
# Daily User Message Statistics
# =========================

MESSAGE_STATISTICS_TABLE = """
CREATE TABLE IF NOT EXISTS message_statistics (
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    statistic_date DATE NOT NULL,

    message_count BIGINT NOT NULL DEFAULT 0,

    PRIMARY KEY (guild_id, user_id, statistic_date)
);
"""


# =========================
# Daily User Voice Statistics
# =========================

VOICE_STATISTICS_TABLE = """
CREATE TABLE IF NOT EXISTS voice_statistics (
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    statistic_date DATE NOT NULL,

    voice_seconds BIGINT NOT NULL DEFAULT 0,

    PRIMARY KEY (guild_id, user_id, statistic_date)
);
"""


# =========================
# Daily Channel Message Statistics
# =========================

CHANNEL_MESSAGE_STATISTICS_TABLE = """
CREATE TABLE IF NOT EXISTS channel_message_statistics (
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    statistic_date DATE NOT NULL,

    message_count BIGINT NOT NULL DEFAULT 0,

    PRIMARY KEY (guild_id, channel_id, statistic_date)
);
"""


# =========================
# Daily Channel Voice Statistics
# =========================

CHANNEL_VOICE_STATISTICS_TABLE = """
CREATE TABLE IF NOT EXISTS channel_voice_statistics (
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    statistic_date DATE NOT NULL,

    voice_seconds BIGINT NOT NULL DEFAULT 0,

    PRIMARY KEY (guild_id, channel_id, statistic_date)
);
"""


# =========================
# Processed Messages
# =========================

PROCESSED_MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS processed_messages (
    guild_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,

    message_created_at TIMESTAMPTZ NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (guild_id, message_id)
);
"""


# =========================
# Message Recovery State
# =========================

MESSAGE_RECOVERY_STATE_TABLE = """
CREATE TABLE IF NOT EXISTS message_recovery_state (
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,

    last_scanned_at TIMESTAMPTZ,

    PRIMARY KEY (guild_id, channel_id)
);
"""


# =========================
# Recovery Requests
# =========================
#
# On-demand rescans requested from the dashboard (see
# dashboard/backend/api/routes/recovery.py). A row here means "please
# rescan this channel"; RECOVERY_REQUEST_POLL_LOOP in bot/events.py
# picks it up, runs the same scan logic as the automatic
# post-reconnect recovery, and deletes the row when done. The dashboard
# never touches message_recovery_state directly — it only ever adds a
# request here, so the bot stays the single writer of recovery state.

RECOVERY_REQUESTS_TABLE = """
CREATE TABLE IF NOT EXISTS recovery_requests (
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,

    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    requested_by BIGINT,

    PRIMARY KEY (guild_id, channel_id)
);
"""


# =========================
# Warning History
# =========================

WARNING_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS warning_history (
    warning_id BIGSERIAL PRIMARY KEY,

    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    moderator_id BIGINT NOT NULL,

    reason TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""




# =========================
# Performance Indexes
# =========================

# The primary keys are excellent for point lookups, but leaderboard/date-range
# queries filter by guild + date. These indexes keep those queries fast as the
# statistics tables grow.
STATISTICS_INDEXES = [
    """CREATE INDEX IF NOT EXISTS idx_message_statistics_guild_date
       ON message_statistics (guild_id, statistic_date, user_id);""",
    """CREATE INDEX IF NOT EXISTS idx_voice_statistics_guild_date
       ON voice_statistics (guild_id, statistic_date, user_id);""",
    """CREATE INDEX IF NOT EXISTS idx_channel_message_statistics_guild_date
       ON channel_message_statistics (guild_id, statistic_date, channel_id);""",
    """CREATE INDEX IF NOT EXISTS idx_channel_voice_statistics_guild_date
       ON channel_voice_statistics (guild_id, statistic_date, channel_id);""",
    """CREATE INDEX IF NOT EXISTS idx_processed_messages_processed_at
       ON processed_messages (processed_at);""",
]
