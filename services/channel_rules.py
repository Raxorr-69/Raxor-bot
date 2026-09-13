import re


# =========================
# Image Detection
# =========================

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
}


def is_image_attachment(attachment) -> bool:
    """Check whether an attachment is an image."""

    content_type = attachment.content_type

    if content_type:
        return content_type.startswith("image/")

    filename = attachment.filename.lower()

    return any(
        filename.endswith(extension)
        for extension in IMAGE_EXTENSIONS
    )


def message_contains_image(message) -> bool:
    """Check whether a message contains an image."""

    return any(
        is_image_attachment(attachment)
        for attachment in message.attachments
    )


# =========================
# Clip Detection
# =========================

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".webm",
    ".mkv",
    ".avi",
}


def is_video_attachment(attachment) -> bool:
    """Check whether an attachment is a video."""

    content_type = attachment.content_type

    if content_type:
        return content_type.startswith("video/")

    filename = attachment.filename.lower()

    return any(
        filename.endswith(extension)
        for extension in VIDEO_EXTENSIONS
    )


def message_contains_clip(message) -> bool:
    """
    Check whether a message contains a video/clip attachment.

    A video attachment is treated as a clip.
    """

    return any(
        is_video_attachment(attachment)
        for attachment in message.attachments
    )


# =========================
# Restriction Checks
# =========================

def violates_image_only(message) -> bool:
    """
    Return True when an image-only channel receives
    a message without an image.
    """

    return not message_contains_image(message)


def violates_clips_only(message) -> bool:
    """
    Return True when a clips-only channel receives
    a message without a video/clip.
    """

    return not message_contains_clip(message)


# =========================
# Text Detection
# =========================

def has_text_content(content: str) -> bool:
    """Check whether message content contains meaningful text."""

    if not content:
        return False

    return bool(content.strip())


def is_text_only_message(message) -> bool:
    """Check whether a message contains text but no attachments."""

    return (
        has_text_content(message.content)
        and not message.attachments
    )
