"""
HTML and URL utility functions for safe output formatting.
"""
from __future__ import annotations


def escape_html(text: str | None) -> str:
    """Escape special HTML characters to prevent injection."""
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def safe_url(url: str | None) -> str:
    """Validate and sanitize a URL for safe use in HTML attributes."""
    from config import logger  # local import để tránh circular dependency
    if not url:
        return "#"
    if not url.startswith(("https://", "http://")):
        logger.warning("Rejected non-http URL in safe_url: %.120s", url)
        return "#"
    return url.replace('"', "%22").replace("'", "%27")
