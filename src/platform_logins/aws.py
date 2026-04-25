from __future__ import annotations

from typing import Dict, List

from src.human_behavior import human_like_typing, human_like_click, random_human_wait
from src.platform_logins.base import BasePlatformLogin, TwoFactorAuthError


class AWSLogin(BasePlatformLogin):
    LOGIN_URL = "https://signin.aws.amazon.com/signin"
    COOKIE_DOMAINS = [".amazon.com", "signin.aws.amazon.com"]
    AUTH_INDICATOR_SELECTORS = [
        "[data-testid='awsc-concierge-input']",
        "#nav-usernameMenu",
        ".awsc-nav-account-menu",
    ]

    async def login(self, page, credentials: Dict[str, str]) -> None:
        """Log in to AWS."""
        await page.goto(self.LOGIN_URL, wait_until="networkidle")
        await random_human_wait(1.0, 2.0)

        await human_like_typing(page, "#resolving_input", credentials["username"])
        await random_human_wait(0.5, 1.0)
        await human_like_click(page, "#next_button")
        await page.wait_for_load_state("networkidle")
        await random_human_wait(2.0, 3.0)

        await human_like_typing(page, "#password", credentials["password"])
        await random_human_wait(0.5, 1.0)
        await human_like_click(page, "#signin_button")
        await page.wait_for_load_state("networkidle")
        await random_human_wait(2.0, 4.0)

        if await self._detect_2fa(page):
            raise TwoFactorAuthError("AWS MFA detected")

    async def is_logged_in(self, page) -> bool:
        """Check if logged in to AWS."""
        for selector in self.AUTH_INDICATOR_SELECTORS:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    return True
            except Exception:
                continue
        return False
