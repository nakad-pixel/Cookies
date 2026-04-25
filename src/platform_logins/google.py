from __future__ import annotations

from typing import Dict, List

from src.human_behavior import human_like_typing, human_like_click, random_human_wait
from src.platform_logins.base import BasePlatformLogin, TwoFactorAuthError


class GoogleLogin(BasePlatformLogin):
    LOGIN_URL = "https://accounts.google.com/signin"
    COOKIE_DOMAINS = [".google.com", "accounts.google.com"]
    AUTH_INDICATOR_SELECTORS = [
        "img[alt*='profile']",
        "a[aria-label*='Google Account']",
        "[data-testid='account-avatar']",
        ".gb_Ba",  # Google apps menu indicator
    ]

    async def login(self, page, credentials: Dict[str, str]) -> None:
        """Log in to Google."""
        await page.goto(self.LOGIN_URL, wait_until="networkidle")
        await random_human_wait(1.0, 2.0)

        # Email identifier
        await human_like_typing(page, "#identifierId", credentials["username"])
        await random_human_wait(0.5, 1.0)
        await human_like_click(page, "*[role='button']:has-text('Next'), #identifierNext")
        await page.wait_for_load_state("networkidle")
        await random_human_wait(2.0, 3.0)

        # Password
        password_selector = "input[type='password'], input[name='password']"
        await human_like_typing(page, password_selector, credentials["password"])
        await random_human_wait(0.5, 1.0)
        await human_like_click(page, "*[role='button']:has-text('Next'), #passwordNext")
        await page.wait_for_load_state("networkidle")
        await random_human_wait(2.0, 4.0)

        if await self._detect_2fa(page):
            raise TwoFactorAuthError("Google 2FA detected")

        # Handle "Skip" or "Stay signed in?" prompts
        skip_selectors = [
            "button:has-text('Skip')",
            "button:has-text('No thanks')",
            "button:has-text('Not now')",
        ]
        for selector in skip_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await human_like_click(page, selector)
                    await random_human_wait(1.0, 2.0)
            except Exception:
                continue

    async def is_logged_in(self, page) -> bool:
        """Check if logged in to Google."""
        for selector in self.AUTH_INDICATOR_SELECTORS:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    return True
            except Exception:
                continue
        return False
