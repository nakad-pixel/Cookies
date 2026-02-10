from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.cleanup import SecureWiper
from src.logger import log_2fa_detected, setup_logger

try:
    from playwright.sync_api import sync_playwright, Page
except ImportError:  # pragma: no cover - optional dependency
    sync_playwright = None
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
    success: bool = False
    error_message: Optional[str] = None

    def wipe_cookies(self) -> None:
        """Securely wipe all cookie values."""
        for cookie in self.cookies:
            cookie.wipe()
        self.cookies = []


class TwoFactorAuthError(Exception):
    """Raised when 2FA is detected during login."""
    pass


class BrowserAutomation:
    """Browser automation with 2FA detection and stealth features."""

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

    def __init__(self, headless: bool = True) -> None:
        self.headless = headless
        self.logger = setup_logger("browser-automation")

    def _check_for_2fa(self, page) -> bool:
        """Check if the current page indicates 2FA is required.

        Args:
            page: Playwright page object

        Returns:
            True if 2FA is detected
        """
        # Check page content for 2FA keywords
        content = page.content().lower()
        for pattern in self.TWO_FA_PATTERNS:
            if pattern in content:
                self.logger.debug(f"2FA pattern detected: {pattern}")
                return True

        # Check for 2FA input fields
        for selector in self.TWO_FA_SELECTORS:
            try:
                if page.locator(selector).count() > 0:
                    self.logger.debug(f"2FA selector found: {selector}")
                    return True
            except Exception:
                continue

        # Check page title for 2FA indicators
        title = page.title().lower()
        title_indicators = ["two-factor", "2fa", "authentication", "verification", "security code"]
        for indicator in title_indicators:
            if indicator in title:
                self.logger.debug(f"2FA indicator in title: {indicator}")
                return True

        return False

    def extract_cookies(
        self,
        url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        platform: str = "unknown"
    ) -> ExtractionResult:
        """Extract cookies from a platform with 2FA detection.

        Args:
            url: The URL to navigate to
            username: Optional username for login
            password: Optional password for login
            platform: Platform name for logging

        Returns:
            ExtractionResult with cookies or 2FA detection status
        """
        if sync_playwright is None:
            raise RuntimeError("Playwright is not installed")

        result = ExtractionResult()

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    viewport={
                        "width": random.choice([1280, 1366, 1440]),
                        "height": random.choice([720, 768, 900])
                    },
                    timezone_id=random.choice(["UTC", "America/New_York", "Europe/London"]),
                    user_agent=self._get_random_user_agent(),
                )

                # Stealth: disable webdriver property
                context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)

                page = context.new_page()
                page.goto(url, wait_until="networkidle")

                # Check for 2FA immediately after page load
                if self._check_for_2fa(page):
                    result.has_2fa = True
                    log_2fa_detected(self.logger, platform)
                    browser.close()
                    return result

                # If credentials provided, attempt login
                if username and password:
                    # This is a simplified login flow - platforms may vary
                    # The actual implementation would need platform-specific selectors
                    login_result = self._attempt_login(page, username, password, platform)

                    if login_result.get("has_2fa", False):
                        result.has_2fa = True
                        log_2fa_detected(self.logger, platform)
                        browser.close()
                        return result

                    # Check again after login attempt
                    if self._check_for_2fa(page):
                        result.has_2fa = True
                        log_2fa_detected(self.logger, platform)
                        browser.close()
                        return result

                # Extract cookies
                raw_cookies = context.cookies()
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

                browser.close()

        except TwoFactorAuthError:
            result.has_2fa = True
            log_2fa_detected(self.logger, platform)
        except Exception as e:
            result.error_message = str(e)
            self.logger.error(f"Extraction failed: {e}")

        return result

    def _attempt_login(
        self,
        page,
        username: str,
        password: str,
        platform: str
    ) -> Dict[str, bool]:
        """Attempt to log in to the platform.

        This is a generic implementation. Production would need platform-specific selectors.

        Returns:
            Dict with 'success' and 'has_2fa' keys
        """
        result = {"success": False, "has_2fa": False}

        try:
            # Common username field selectors
            username_selectors = [
                'input[name="username"]',
                'input[name="login"]',
                'input[name="email"]',
                'input[type="email"]',
                'input[id="username"]',
                'input[id="login"]',
            ]

            # Common password field selectors
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[id="password"]',
            ]

            # Find and fill username
            for selector in username_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        page.locator(selector).fill(username)
                        break
                except Exception:
                    continue

            # Find and fill password
            for selector in password_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        page.locator(selector).fill(password)
                        break
                except Exception:
                    continue

            # Click submit (common patterns)
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Sign in")',
                'button:has-text("Log in")',
                'button:has-text("Login")',
            ]

            for selector in submit_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        page.locator(selector).click()
                        page.wait_for_load_state("networkidle")
                        break
                except Exception:
                    continue

            # Check for 2FA after login attempt
            if self._check_for_2fa(page):
                result["has_2fa"] = True
                return result

            result["success"] = True

        except Exception as e:
            self.logger.error(f"Login attempt failed: {e}")

        return result

    def _get_random_user_agent(self) -> str:
        """Get a random user agent to avoid detection."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        return random.choice(user_agents)

    def validate_cookies(self, url: str, cookies: List[CookieData]) -> bool:
        """Validate that cookies work for accessing the given URL.

        Args:
            url: URL to test
            cookies: Cookies to use

        Returns:
            True if cookies are valid
        """
        if sync_playwright is None:
            raise RuntimeError("Playwright is not installed")

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=self.headless)
                context = browser.new_context()
                context.add_cookies(
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
                page = context.new_page()
                response = page.goto(url, wait_until="domcontentloaded")
                browser.close()
                return bool(response) and response.ok
        except Exception as e:
            self.logger.error(f"Cookie validation failed: {e}")
            return False
