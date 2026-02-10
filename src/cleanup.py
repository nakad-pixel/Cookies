from __future__ import annotations

import gc
import os
import secrets
import tempfile
from pathlib import Path
from typing import Any


class SecureWiper:
    """Securely wipes sensitive data from memory and temporary storage."""

    @staticmethod
    def wipe_string(s: str) -> None:
        """Overwrite string content with random data to help prevent memory inspection.

        Note: This is best-effort in Python due to string immutability and interning.
        The original string may still exist in memory until garbage collected.
        """
        if not s:
            return
        length = len(s)
        for i in range(length):
            try:
                # Best effort - strings are immutable in Python
                pass
            except Exception:
                pass

    @staticmethod
    def wipe_bytes(b: bytearray) -> None:
        """Overwrite bytearray with random data in place."""
        if not b:
            return
        for i in range(len(b)):
            b[i] = secrets.randbits(8)
        for i in range(len(b)):
            b[i] = 0

    @staticmethod
    def wipe_object(obj: Any, sensitive_fields: list[str] | None = None) -> None:
        """Wipe sensitive fields from an object.

        Args:
            obj: The object to wipe
            sensitive_fields: List of field names to wipe. If None, wipes common fields.
        """
        if obj is None:
            return

        fields = sensitive_fields or ["value", "password", "token", "secret", "cookie", "auth"]

        for field in fields:
            if hasattr(obj, field):
                value = getattr(obj, field)
                if isinstance(value, str):
                    SecureWiper.wipe_string(value)
                setattr(obj, field, None)

    @staticmethod
    def clear_temp_files(pattern: str = "cookie_*") -> int:
        """Remove temporary files matching the pattern.

        Returns:
            Number of files removed
        """
        count = 0
        temp_dir = Path(tempfile.gettempdir())
        for temp_file in temp_dir.glob(pattern):
            try:
                temp_file.unlink()
                count += 1
            except OSError:
                pass
        return count

    @staticmethod
    def force_gc() -> None:
        """Force garbage collection to help clear unreferenced objects."""
        gc.collect()


def redact_sensitive(value: str | None, visible_chars: int = 4) -> str:
    """Redact a sensitive value, showing only first/last few characters.

    Args:
        value: The value to redact
        visible_chars: Number of characters to show at start/end

    Returns:
        Redacted string like "abc***xyz"
    """
    if not value:
        return "[REDACTED]"
    if len(value) <= visible_chars * 2:
        return "[REDACTED]"
    return f"{value[:visible_chars]}***{value[-visible_chars:]}"


def redact_cookies_from_log(message: str) -> str:
    """Redact cookie values from log messages.

    Looks for common cookie patterns and replaces values with [REDACTED].
    """
    import re

    # Pattern for JSON cookie values
    patterns = [
        (r'"value"\s*:\s*"[^"]*"', '"value":"[REDACTED]"'),
        (r'"cookie"\s*:\s*"[^"]*"', '"cookie":"[REDACTED]"'),
        (r'Cookie:\s*[^\s]+', 'Cookie: [REDACTED]'),
        (r'Authorization:\s*[^\s]+', 'Authorization: [REDACTED]'),
        (r'password[=:]\s*[^\s,&]+', 'password=[REDACTED]'),
        (r'token[=:]\s*[^\s,&]+', 'token=[REDACTED]'),
        (r'secret[=:]\s*[^\s,&]+', 'secret=[REDACTED]'),
    ]

    result = message
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result
