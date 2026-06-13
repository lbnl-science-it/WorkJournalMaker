# ABOUTME: Utilities for safe error responses that avoid leaking internal details.
# ABOUTME: Provides a sanitize function for stored error strings before HTTP serialization.
"""Error sanitization utilities for API responses."""

from typing import Optional


def sanitize_error_message(raw: Optional[str], *, generic: str = "An error occurred") -> Optional[str]:
    """Replace a raw error string with a generic message safe for API responses.

    Returns None when raw is None (no error occurred), otherwise returns the
    generic message regardless of raw content, preventing internal details
    from leaking to clients.
    """
    if raw is None:
        return None
    return generic
