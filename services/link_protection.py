import re


# =========================
# Link Detection
# =========================

URL_PATTERN = re.compile(
    r"(?i)\b(?:https?://|www\.)[^\s<>()]+"
)


DISCORD_INVITE_PATTERN = re.compile(
    r"(?i)\b(?:https?://)?(?:www\.)?"
    r"(?:discord\.gg|discord\.com/invite|discordapp\.com/invite)"
    r"/[A-Za-z0-9-]+"
)


# =========================
# Protection Actions
# =========================

ALLOWED_LINK_ACTIONS = {
    "warn",
    "delete",
    "timeout",
}


def is_valid_link_action(action: str) -> bool:
    """Check whether a link-protection action is supported."""

    return action in ALLOWED_LINK_ACTIONS


def get_link_action(action: str) -> str:
    """Return a valid link-protection action."""

    if not is_valid_link_action(action):
        return "warn"

    return action


# =========================
# URL Detection
# =========================

def contains_link(content: str) -> bool:
    """Check whether a message contains an external URL."""

    if not content:
        return False

    return URL_PATTERN.search(content) is not None


def contains_discord_invite(content: str) -> bool:
    """Check whether a message contains a Discord invite."""

    if not content:
        return False

    return DISCORD_INVITE_PATTERN.search(content) is not None


# =========================
# Protection Check
# =========================

def is_link_protected_message(
    content: str,
    protect_links: bool,
    protect_invites: bool,
) -> bool:
    """
    Check whether a message violates the configured
    link or Discord-invite protection.
    """

    if not content:
        return False

    if protect_invites and contains_discord_invite(content):
        return True

    if protect_links and contains_link(content):
        return True

    return False


# =========================
# Action Resolver
# =========================

def get_protection_type(content: str) -> str | None:
    """
    Return the type of protected content found in a message.

    Possible values:
    - "invite"
    - "link"
    - None
    """

    if not content:
        return None

    if contains_discord_invite(content):
        return "invite"

    if contains_link(content):
        return "link"

    return None
