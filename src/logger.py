from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict


# Sensitive field patterns to redact
SENSITIVE_PATTERNS = [
    re.compile(r'"value"\s*:\s*"[^"]*"', re.IGNORECASE),
    re.compile(r'"cookie"\s*:\s*"[^"]*"', re.IGNORECASE),
    re.compile(r'Cookie:\s*[^\s]+', re.IGNORECASE),
    re.compile(r'Authorization:\s*Bearer\s+[^\s]+', re.IGNORECASE),
    re.compile(r'password[=:]\s*[^\s,&]+', re.IGNORECASE),
    re.compile(r'token[=:]\s*[^\s,&]+', re.IGNORECASE),
    re.compile(r'secret[=:]\s*[^\s,&]+', re.IGNORECASE),
    re.compile(r'api[_-]?key[=:]\s*[^\s,&]+', re.IGNORECASE),
]

SENSITIVE_KEYS = {
    "value", "cookie", "cookies", "password", "token", "secret",
    "api_key", "apikey", "auth", "authorization", "credential",
    "private_key", "privatekey", "session", "jwt", "bearer"
}


def redact_sensitive_data(data: Any) -> Any:
    """Recursively redact sensitive data from a structure.

    Args:
        data: The data to redact (dict, list, or primitive)

    Returns:
        Redacted copy of the data
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sk in key_lower for sk in SENSITIVE_KEYS):
                if isinstance(value, str) and len(value) > 8:
                    result[key] = f"{value[:3]}***{value[-3:]}"
                else:
                    result[key] = "[REDACTED]"
            else:
                result[key] = redact_sensitive_data(value)
        return result
    elif isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    elif isinstance(data, str):
        # Apply pattern-based redaction
        result = data
        for pattern in SENSITIVE_PATTERNS:
            result = pattern.sub(lambda m: _redact_match(m.group()), result)
        return result
    return data


def _redact_match(match_str: str) -> str:
    """Redact a matched sensitive string, preserving structure."""
    # Try to preserve the key part before the value
    if "=" in match_str:
        key = match_str.split("=")[0]
        return f"{key}=[REDACTED]"
    if ":" in match_str and not match_str.startswith("{"):
        key = match_str.split(":")[0]
        return f"{key}: [REDACTED]"
    if "{" in match_str and "value" in match_str.lower():
        return '"value":"[REDACTED]"'
    return "[REDACTED]"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            # Redact sensitive data from extra fields
            redacted_extra = redact_sensitive_data(record.extra)
            payload.update(redacted_extra)

        # Redact any sensitive data from the final JSON string
        json_str = json.dumps(payload, ensure_ascii=False, default=str)
        return json_str


def setup_logger(name: str, level: str = "INFO", json_output: bool = True) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    if json_output:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def log_event(logger: logging.Logger, message: str, **kwargs: Any) -> None:
    """Log an event with redacted sensitive data."""
    # Redact sensitive values from message
    redacted_message = redact_sensitive_data(message)
    # Redact sensitive data from kwargs
    redacted_kwargs = redact_sensitive_data(kwargs)
    logger.info(redacted_message, extra={"extra": redacted_kwargs})


def log_2fa_detected(logger: logging.Logger, platform: str) -> None:
    """Log that 2FA was detected and the platform is being skipped."""
    log_event(
        logger,
        f"2FA detected on {platform} - skipping (2FA not supported)",
        platform=platform,
        status="skipped",
        reason="2fa_not_supported"
    )


def log_cookie_extraction(logger: logging.Logger, platform: str, cookie_count: int, has_2fa: bool = False) -> None:
    """Log cookie extraction attempt with safe metadata only."""
    if has_2fa:
        log_2fa_detected(logger, platform)
    else:
        log_event(
            logger,
            f"Cookie extraction successful for {platform}",
            platform=platform,
            cookie_count=cookie_count,
            status="success"
        )


def log_secret_injection(logger: logging.Logger, repo: str, secret_name: str) -> None:
    """Log secret injection without revealing the value."""
    log_event(
        logger,
        f"Injected secret to repository",
        repository=repo,
        secret_name=secret_name,
        status="injected"
    )
