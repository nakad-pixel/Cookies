from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class TwoFactorAuthError(Exception):
    """Raised when 2FA is detected during login."""
    pass


class BasePlatformLogin(ABC):
    """Abstract base class for platform-specific login flows."""

    LOGIN_URL: str = ""
    COOKIE_DOMAINS: List[str] = []
    AUTH_INDICATOR_SELECTORS: List[str] = []

    @abstractmethod
    async def login(self, page, credentials: Dict[str, str]) -> None:
        """Perform login on the given page.

        Args:
            page: Patchright page object.
            credentials: Dict with 'username' and 'password' keys.

        Raises:
            TwoFactorAuthError: If 2FA is detected.
        """
        ...

    @abstractmethod
    async def is_logged_in(self, page) -> bool:
        """Check if the user is currently logged in.

        Args:
            page: Patchright page object.

        Returns:
            True if logged in, False otherwise.
        """
        ...

    async def _detect_2fa(self, page) -> bool:
        """Detect if a 2FA prompt is present on the page.

        Args:
            page: Patchright page object.

        Returns:
            True if 2FA is detected.
        """
        two_fa_patterns = [
            "two-factor",
            "two factor",
            "2fa",
            "two-step",
            "authenticator",
            "verification code",
            "security code",
            "sms code",
            "backup code",
            "auth code",
            "enter code",
            "verify your identity",
            "additional verification",
        ]
        selectors = [
            'input[name*="2fa"]',
            'input[name*="code"]',
            'input[name*="otp"]',
            'input[name*="totp"]',
            'input[placeholder*="code" i]',
            'input[placeholder*="authenticator" i]',
            '[data-testid*="two-factor"]',
            '[data-testid*="2fa"]',
        ]

        try:
            content = (await page.content()).lower()
            for pattern in two_fa_patterns:
                if pattern in content:
                    return True
        except Exception:
            pass

        for selector in selectors:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    return True
            except Exception:
                continue

        try:
            title = (await page.title()).lower()
            for indicator in ["two-factor", "2fa", "authentication", "verification", "security code"]:
                if indicator in title:
                    return True
        except Exception:
            pass

        return False
