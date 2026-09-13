def format_duration(seconds: int) -> str:
    """Format seconds into a readable duration."""

    if seconds < 0:
        seconds = 0

    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []

    if days:
        parts.append(f"{days}d")

    if hours:
        parts.append(f"{hours}h")

    if minutes:
        parts.append(f"{minutes}m")

    if seconds or not parts:
        parts.append(f"{seconds}s")

    return " ".join(parts)


def format_number(value: int) -> str:
    """Format a number with thousands separators."""

    return f"{value:,}"


def format_user_id(user_id: int) -> str:
    """Format a Discord user ID for display."""

    return f"<@{user_id}>"


def format_channel_id(channel_id: int) -> str:
    """Format a Discord channel ID for display."""

    return f"<#{channel_id}>"


def truncate_field(text: str, limit: int = 1024) -> str:
    """
    Truncate text to fit inside a Discord embed field.

    Discord rejects embeds with a field value longer than 1024
    characters, so this keeps long lists (roles, members, etc.)
    from causing the whole command to fail.
    """

    if len(text) <= limit:
        return text

    suffix = "…"
    cutoff = limit - len(suffix)

    return text[:cutoff].rstrip(", ") + suffix


