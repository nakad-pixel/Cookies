from __future__ import annotations

from typing import Dict, List

from src.human_behavior import human_like_typing, human_like_click, random_human_wait
from src.platform_logins.base import BasePlatformLogin, TwoFactorAuthError


class GitHubLogin(BasePlatformLogin):
    LOGIN_URL = "https://github.com/login"
    COOKIE_DOMAINS = [".github.com", "github.com"]
    AUTH_INDICATOR_SELECTORS = [
        "[data-testid='global-nav'] img.avatar",
        ".Header-link img.avatar",
        "[aria-label='View profile and more']",
        "img[src*='avatars']",
    ]

    async def login(self, page, credentials: Dict[str, str]) -> None:
        """Log in to GitHub."""
        await page.goto(self.LOGIN_URL, wait_until="networkidle")
        await random_human_wait(1.0, 2.0)

        await human_like_typing(page, "#login_field", credentials["username"])
        await random_human_wait(0.5, 1.0)
        await human_like_typing(page, "#password", credentials["password"])
        await random_human_wait(0.5, 1.0)

        await human_like_click(page, "[name='commit']")
        await page.wait_for_load_state("networkidle")
        await random_human_wait(2.0, 4.0)

        if await self._detect_2fa(page):
            raise TwoFactorAuthError("GitHub 2FA detected")

    async def is_logged_in(self, page) -> bool:
        """Check if logged in to GitHub."""
        for selector in self.AUTH_INDICATOR_SELECTORS:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    return True
            except Exception:
                continue
        return False
