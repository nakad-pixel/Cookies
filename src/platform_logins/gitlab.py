from __future__ import annotations

from typing import Dict, List

from src.human_behavior import human_like_typing, human_like_click, random_human_wait
from src.platform_logins.base import BasePlatformLogin, TwoFactorAuthError


class GitLabLogin(BasePlatformLogin):
    LOGIN_URL = "https://gitlab.com/users/sign_in"
    COOKIE_DOMAINS = [".gitlab.com", "gitlab.com"]
    AUTH_INDICATOR_SELECTORS = [
        ".user-bar",
        ".header-user",
        "[data-qa-selector='user_menu']",
        ".avatar-container",
    ]

    async def login(self, page, credentials: Dict[str, str]) -> None:
        """Log in to GitLab."""
        await page.goto(self.LOGIN_URL, wait_until="networkidle")
        await random_human_wait(1.0, 2.0)

        await human_like_typing(page, "#user_login", credentials["username"])
        await random_human_wait(0.5, 1.0)
        await human_like_typing(page, "#user_password", credentials["password"])
        await random_human_wait(0.5, 1.0)

        await human_like_click(page, ".sign-in-button, [name='commit']")
        await page.wait_for_load_state("networkidle")
        await random_human_wait(2.0, 4.0)

        if await self._detect_2fa(page):
            raise TwoFactorAuthError("GitLab 2FA detected")

    async def is_logged_in(self, page) -> bool:
        """Check if logged in to GitLab."""
        for selector in self.AUTH_INDICATOR_SELECTORS:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    return True
            except Exception:
                continue
        return False
