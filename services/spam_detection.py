from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone


# =========================
# Spam Tracking
# =========================

user_message_history = defaultdict(deque)

# Tracks when each (guild_id, user_id) key was last touched, so
# entries for users who go inactive can be swept out. Without this,
# the dict above grows forever as new users message the bot, even
# after their short-term history has emptied out.
_last_seen = {}
_STALE_AFTER_SECONDS = 3600  # Drop keys untouched for over an hour
_CLEANUP_INTERVAL = 500      # Sweep every N calls instead of every call
_call_counter = 0


def _cleanup_stale_entries(now: datetime) -> None:
    """Remove tracking data for users who haven't messaged recently."""

    stale_keys = [
        key
        for key, last_seen in _last_seen.items()
        if (now - last_seen).total_seconds() > _STALE_AFTER_SECONDS
    ]

    for key in stale_keys:
        user_message_history.pop(key, None)
        _last_seen.pop(key, None)


# =========================
# Message Spam Check
# =========================


def is_message_spam(
    guild_id: int,
    user_id: int,
    limit: int,
    window_seconds: int,
) -> bool:
    """Check whether a user is sending messages too quickly."""

    global _call_counter

    now = datetime.now(timezone.utc)

    key = (guild_id, user_id)

    history = user_message_history[key]

    # Remove messages outside the time window
    while history:
        elapsed = (
            now - history[0]
        ).total_seconds()

        if elapsed <= window_seconds:
            break

        history.popleft()

    # Add current message
    history.append(now)
    _last_seen[key] = now

    # Periodically sweep out stale, inactive users so memory
    # doesn't grow unbounded over the bot's uptime.
    _call_counter += 1
    if _call_counter >= _CLEANUP_INTERVAL:
        _call_counter = 0
        _cleanup_stale_entries(now)

    # Check limit
    return len(history) > limit



# =========================
# Emoji Spam Check
# =========================


def count_emojis(content: str) -> int:
    """Count emoji characters in a message."""

    count = 0

    for character in content:
        if character.isascii():
            continue

        # Basic Unicode emoji range check
        code_point = ord(character)

        if (
            0x1F300 <= code_point <= 0x1FAFF
            or 0x2600 <= code_point <= 0x27BF
        ):
            count += 1

    return count


def is_emoji_spam(
    content: str,
    emoji_limit: int,
) -> bool:
    """Check whether a message contains too many emojis."""

    emoji_count = count_emojis(content)

    return emoji_count > emoji_limit



# =========================
# Spam History Cleanup
# =========================


def clear_user_spam_history(
    guild_id: int,
    user_id: int,
):
    """Clear a user's message spam history."""

    user_message_history.pop(
        (guild_id, user_id),
        None,
    )



# =========================
# Spam Action Validation
# =========================


ALLOWED_SPAM_ACTIONS = {
    "warn",
    "delete",
    "timeout",
}


def is_valid_spam_action(
    action: str,
) -> bool:
    """Check whether a spam action is supported."""

    return action in ALLOWED_SPAM_ACTIONS



# =========================
# pam Action Resolver
# =========================


def get_spam_action(
    action: str,
) -> str:
    """Return a valid spam action."""

    if not is_valid_spam_action(action):
        return "warn"

    return action



# =========================
# Spam Action Handler
# =========================



async def handle_spam_action(
    message,
    action: str,
    timeout_seconds: int = 60,
):
    """Apply the configured action to a spam message."""

    action = get_spam_action(action)

    if action == "warn":
        return "warn"

    if action == "delete":
        try:
            await message.delete()
        except Exception:
            pass

        return "delete"

    if action == "timeout":
        try:
            await message.delete()
        except Exception:
            pass

        try:
            await message.author.timeout(
                timedelta(seconds=timeout_seconds),
                reason="Spam detected",
            )
        except Exception:
            pass

        return "timeout"
