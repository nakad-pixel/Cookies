from __future__ import annotations

from typing import Dict, List

from src.human_behavior import human_like_typing, human_like_click, random_human_wait
from src.platform_logins.base import BasePlatformLogin, TwoFactorAuthError


class AzureLogin(BasePlatformLogin):
    LOGIN_URL = "https://login.microsoftonline.com/"
    COOKIE_DOMAINS = [".microsoftonline.com", "login.microsoftonline.com"]
    AUTH_INDICATOR_SELECTORS = [
        "#id_n",
        "#user-display-name",
        ".ms-Persona",
        "[role='banner'] img[src*='photo']",
    ]

    async def login(self, page, credentials: Dict[str, str]) -> None:
        """Log in to Azure."""
        await page.goto(self.LOGIN_URL, wait_until="networkidle")
        await random_human_wait(1.0, 2.0)

        await human_like_typing(page, "#i0116", credentials["username"])
        await random_human_wait(0.5, 1.0)
        await human_like_click(page, "#idSIButton9")
        await page.wait_for_load_state("networkidle")
        await random_human_wait(2.0, 3.0)

        await human_like_typing(page, "#i0118", credentials["password"])
        await random_human_wait(0.5, 1.0)
        await human_like_click(page, "#idSIButton9")
        await page.wait_for_load_state("networkidle")
        await random_human_wait(2.0, 4.0)

        if await self._detect_2fa(page):
            raise TwoFactorAuthError("Azure MFA detected")

        # Handle "Stay signed in?"
        stay_signed_selectors = [
            "#idBtn_Back",  # No
            "#idSIButton9",  # Yes
        ]
        for selector in stay_signed_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await human_like_click(page, selector)
                    await random_human_wait(1.0, 2.0)
                    break
            except Exception:
                continue

    async def is_logged_in(self, page) -> bool:
        """Check if logged in to Azure."""
        for selector in self.AUTH_INDICATOR_SELECTORS:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    return True
            except Exception:
                continue
        return False
