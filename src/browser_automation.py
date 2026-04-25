from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from src.browser_context import BrowserContextManager
from src.captcha_detector import CaptchaDetector, CaptchaResult
from src.cleanup import SecureWiper
from src.header_fingerprinter import HeaderFingerprinter
from src.human_behavior import (
    emulate_scroll,
    human_like_click,
    human_like_typing,
    random_human_wait,
)
from src.logger import log_2fa_detected, setup_logger
from src.platform_logins import get_platform_login
from src.platform_logins.base import TwoFactorAuthError
from src.stealth_config import STEALTH_INIT_SCRIPTS, STEALTH_LAUNCH_ARGS, get_fingerprint

try:
    from patchright.async_api import async_playwright, Browser, BrowserContext, Page
except ImportError:  # pragma: no cover - optional dependency
    async_playwright = None
    Browser = None
    BrowserContext = None
    Page = None


@dataclass
class CookieData:
    name: str
    value: str
    domain: str
    expires: int | None = None
    secure: bool = True
    http_only: bool = True

    def wipe(self) -> None:
        """Securely wipe the cookie value from memory."""
        SecureWiper.wipe_string(self.value)
        self.value = ""


@dataclass
class ExtractionResult:
    """Result of cookie extraction attempt."""
    cookies: List[CookieData] = field(default_factory=list)
    has_2fa: bool = False
    has_captcha: bool = False
    captcha_result: Optional[CaptchaResult] = None
    success: bool = False
    error_message: Optional[str] = None

    def wipe_cookies(self) -> None:
        """Securely wipe all cookie values."""
        for cookie in self.cookies:
            cookie.wipe()
        self.cookies = []


class BrowserAutomation:
    """Async browser automation with anti-detection, human behavior, and CAPTCHA detection."""

    # 2FA detection patterns - look for these in page content
    TWO_FA_PATTERNS = [
        "two-factor",
        "two factor",
        "2fa",
        "2 fa",
        "two-step",
        "two step",
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

    # Selectors that might indicate 2FA input fields
    TWO_FA_SELECTORS = [
        'input[name*="2fa"]',
        'input[name*="two"]',
        'input[name*="code"]',
        'input[name*="otp"]',
        'input[name*="totp"]',
        'input[placeholder*="code" i]',
        'input[placeholder*="authenticator" i]',
        '[data-testid*="two-factor"]',
        '[data-testid*="2fa"]',
    ]

    def __init__(
        self,
        headless: bool = True,
        profile_dir: str = "data/profiles",
        enable_har: bool = False,
        har_dir: str = "data/har",
        enable_tracing: bool = False,
        tracing_dir: str = "data/traces",
    ) -> None:
        self.headless = headless
        self.logger = setup_logger("browser-automation")
        self.context_manager = BrowserContextManager(profile_dir)
        self.enable_har = enable_har
        self.har_dir = Path(har_dir)
        self.enable_tracing = enable_tracing
        self.tracing_dir = Path(tracing_dir)
        self._browser: Optional[Browser] = None
        self._playwright = None

    async def _launch_browser(self, platform: str = "generic") -> Browser:
        if async_playwright is None:
            raise RuntimeError("patchright is not installed")

        if self._browser is not None:
            return self._browser

        self._playwright = await async_playwright().start()
        profile_path = self.context_manager.ensure_profile(platform)

        args = list(STEALTH_LAUNCH_ARGS)
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=args,
        )
        return self._browser

    async def _new_context(self, platform: str = "generic") -> BrowserContext:
        browser = await self._launch_browser(platform)
        fingerprint = get_fingerprint(platform)
        profile_path = self.context_manager.ensure_profile(platform)

        har_path = None
        if self.enable_har:
            self.har_dir.mkdir(parents=True, exist_ok=True)
            har_path = self.har_dir / f"{platform}_{random.randint(1000, 9999)}.har"

        context = await browser.new_context(
            viewport=fingerprint.viewport,
            user_agent=fingerprint.user_agent,
            locale=fingerprint.locale,
            timezone_id=fingerprint.timezone,
            color_scheme=fingerprint.color_scheme,
            java_script_enabled=True,
            bypass_csp=True,
            storage_state=str(profile_path / "storage_state.json") if (profile_path / "storage_state.json").exists() else None,
            record_har_path=str(har_path) if har_path else None,
        )

        await context.add_init_script(STEALTH_INIT_SCRIPTS)

        if self.enable_tracing:
            self.tracing_dir.mkdir(parents=True, exist_ok=True)
            trace_path = self.tracing_dir / f"{platform}_{random.randint(1000, 9999)}.zip"
            await context.tracing.start(screenshots=True, snapshots=True, sources=True)
            context._cg_trace_path = str(trace_path)  # type: ignore[attr-defined]

        return context

    async def _close_context(self, context: BrowserContext) -> None:
        if hasattr(context, "_cg_trace_path"):
            try:
                await context.tracing.stop(path=context._cg_trace_path)  # type: ignore[attr-defined]
            except Exception:
                pass
        try:
            await context.close()
        except Exception:
            pass

    async def extract_cookies(
        self,
        url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        platform: str = "unknown",
    ) -> ExtractionResult:
        """Extract cookies from a platform with 2FA and CAPTCHA detection.

        Args:
            url: The URL to navigate to.
            username: Optional username for login.
            password: Optional password for login.
            platform: Platform name for logging and profile selection.

        Returns:
            ExtractionResult with cookies, 2FA/CAPTCHA detection status.
        """
        if async_playwright is None:
            raise RuntimeError("patchright is not installed")

        result = ExtractionResult()
        context = None

        try:
            context = await self._new_context(platform)
            page = await context.new_page()

            # Set extra headers for fingerprint randomization
            fingerprinter = HeaderFingerprinter()
            headers = fingerprinter.get_random_headers(platform)
            await page.set_extra_http_headers(headers)

            await page.goto(url, wait_until="networkidle")
            await random_human_wait(2.0, 4.0)
            await emulate_scroll(page, max_scrolls=3)

            # CAPTCHA detection
            captcha = await CaptchaDetector.detect_any(page)
            if captcha.present:
                result.has_captcha = True
                result.captcha_result = captcha
                self.logger.warning(f"CAPTCHA detected: {captcha.type} on {platform}")
                await self._close_context(context)
                return result

            # 2FA detection
            if await self._check_for_2fa(page):
                result.has_2fa = True
                log_2fa_detected(self.logger, platform)
                await self._close_context(context)
                return result

            # Attempt login if credentials provided
            if username and password:
                try:
                    login_handler = get_platform_login(platform)
                    await login_handler.login(page, {"username": username, "password": password})
                    await random_human_wait(2.0, 4.0)
                except TwoFactorAuthError:
                    result.has_2fa = True
                    log_2fa_detected(self.logger, platform)
                    await self._close_context(context)
                    return result
                except Exception as login_exc:
                    self.logger.warning(f"Platform login failed for {platform}: {login_exc}")
                    # Fallback to generic login attempt
                    await self._attempt_generic_login(page, username, password, platform)

                # Re-check 2FA after login
                if await self._check_for_2fa(page):
                    result.has_2fa = True
                    log_2fa_detected(self.logger, platform)
                    await self._close_context(context)
                    return result

            # Extract cookies
            raw_cookies = await context.cookies()
            result.cookies = [
                CookieData(
                    name=cookie["name"],
                    value=cookie["value"],
                    domain=cookie.get("domain", ""),
                    expires=cookie.get("expires"),
                    secure=cookie.get("secure", True),
                    http_only=cookie.get("httpOnly", True),
                )
                for cookie in raw_cookies
            ]
            result.success = True

            # Persist storage state for next run
            profile_path = self.context_manager.ensure_profile(platform)
            storage_state_path = profile_path / "storage_state.json"
            try:
                await context.storage_state(path=str(storage_state_path))
            except Exception:
                pass

            await self._close_context(context)

        except TwoFactorAuthError:
            result.has_2fa = True
            log_2fa_detected(self.logger, platform)
        except Exception as e:
            result.error_message = str(e)
            self.logger.error(f"Extraction failed: {e}")
            if context:
                await self._close_context(context)

        return result

    async def _check_for_2fa(self, page: Page) -> bool:
        """Check if the current page indicates 2FA is required."""
        try:
            content = (await page.content()).lower()
            for pattern in self.TWO_FA_PATTERNS:
                if pattern in content:
                    self.logger.debug(f"2FA pattern detected: {pattern}")
                    return True
        except Exception:
            pass

        for selector in self.TWO_FA_SELECTORS:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    self.logger.debug(f"2FA selector found: {selector}")
                    return True
            except Exception:
                continue

        try:
            title = (await page.title()).lower()
            title_indicators = ["two-factor", "2fa", "authentication", "verification", "security code"]
            for indicator in title_indicators:
                if indicator in title:
                    self.logger.debug(f"2FA indicator in title: {indicator}")
                    return True
        except Exception:
            pass

        return False

    async def _attempt_generic_login(
        self,
        page: Page,
        username: str,
        password: str,
        platform: str,
    ) -> Dict[str, bool]:
        """Generic fallback login attempt using common selectors."""
        result = {"success": False, "has_2fa": False}

        username_selectors = [
            'input[name="username"]',
            'input[name="login"]',
            'input[name="email"]',
            'input[type="email"]',
            'input[id="username"]',
            'input[id="login"]',
        ]
        password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
            'input[id="password"]',
        ]
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Sign in")',
            'button:has-text("Log in")',
            'button:has-text("Login")',
        ]

        for selector in username_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await human_like_typing(page, selector, username)
                    break
            except Exception:
                continue

        await random_human_wait(0.5, 1.0)

        for selector in password_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await human_like_typing(page, selector, password)
                    break
            except Exception:
                continue

        await random_human_wait(0.5, 1.0)

        for selector in submit_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await human_like_click(page, selector)
                    await page.wait_for_load_state("networkidle")
                    break
            except Exception:
                continue

        if await self._check_for_2fa(page):
            result["has_2fa"] = True
            return result

        result["success"] = True
        return result

    async def validate_cookies(self, url: str, cookies: List[CookieData]) -> bool:
        """Validate that cookies work for accessing the given URL.

        Args:
            url: URL to test.
            cookies: Cookies to use.

        Returns:
            True if cookies are valid.
        """
        if async_playwright is None:
            raise RuntimeError("patchright is not installed")

        context = None
        try:
            context = await self._new_context()
            await context.add_cookies(
                [
                    {
                        "name": cookie.name,
                        "value": cookie.value,
                        "domain": cookie.domain,
                        "path": "/",
                        "secure": cookie.secure,
                        "httpOnly": cookie.http_only,
                        "expires": cookie.expires,
                    }
                    for cookie in cookies
                ]
            )
            page = await context.new_page()
            response = await page.goto(url, wait_until="domcontentloaded")
            await self._close_context(context)
            return bool(response) and response.ok
        except Exception as e:
            self.logger.error(f"Cookie validation failed: {e}")
            if context:
                await self._close_context(context)
            return False

    async def close(self) -> None:
        """Close the browser and stop playwright."""
        if self._browser is not None:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._playwright is not None:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
