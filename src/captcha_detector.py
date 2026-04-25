from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class CaptchaResult:
    type: str
    present: bool
    details: Optional[str] = None


class CaptchaDetector:
    """Detect various CAPTCHA and challenge systems on a page."""

    @staticmethod
    async def detect_recaptcha(page) -> CaptchaResult:
        """Detect reCAPTCHA presence."""
        selectors = [
            'iframe[title*="reCAPTCHA"]',
            '.g-recaptcha',
            '#recaptcha',
            'iframe[src*="recaptcha"]',
        ]
        for selector in selectors:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    return CaptchaResult(type="recaptcha", present=True, details=selector)
            except Exception:
                continue
        return CaptchaResult(type="recaptcha", present=False)

    @staticmethod
    async def detect_hcaptcha(page) -> CaptchaResult:
        """Detect hCaptcha presence."""
        selectors = [
            '.h-captcha',
            'iframe[src*="hcaptcha"]',
            'div[data-hcaptcha-widget-id]',
        ]
        for selector in selectors:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    return CaptchaResult(type="hcaptcha", present=True, details=selector)
            except Exception:
                continue
        return CaptchaResult(type="hcaptcha", present=False)

    @staticmethod
    async def detect_cloudflare_turnstile(page) -> CaptchaResult:
        """Detect Cloudflare Turnstile presence."""
        selectors = [
            'iframe[src*="challenges.cloudflare"]',
            '.cf-turnstile',
            'input[name="cf-turnstile-response"]',
        ]
        for selector in selectors:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    return CaptchaResult(type="cloudflare_turnstile", present=True, details=selector)
            except Exception:
                continue
        return CaptchaResult(type="cloudflare_turnstile", present=False)

    @staticmethod
    async def detect_js_challenge(page) -> CaptchaResult:
        """Detect JavaScript challenge pages (Cloudflare / Imperva)."""
        try:
            title = await page.title()
        except Exception:
            title = ""

        try:
            content = await page.content()
        except Exception:
            content = ""

        indicators = [
            "checking your browser",
            "please wait",
            "ddos protection",
            "challenge",
            "ray id",
            "cloudflare",
            "imperva",
            "security check",
        ]

        title_lower = title.lower()
        content_lower = content.lower()

        for indicator in indicators:
            if indicator in title_lower or indicator in content_lower:
                return CaptchaResult(type="js_challenge", present=True, details=indicator)

        # Check for specific scripts
        script_selectors = [
            'script[src*="challenges.cloudflare"]',
            'script[src*="imperva"]',
            'script[src*="challenge"]',
        ]
        for selector in script_selectors:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    return CaptchaResult(type="js_challenge", present=True, details=selector)
            except Exception:
                continue

        return CaptchaResult(type="js_challenge", present=False)

    @staticmethod
    async def detect_any(page) -> CaptchaResult:
        """Run all detectors and return the first positive match."""
        detectors = [
            CaptchaDetector.detect_recaptcha,
            CaptchaDetector.detect_hcaptcha,
            CaptchaDetector.detect_cloudflare_turnstile,
            CaptchaDetector.detect_js_challenge,
        ]
        for detector in detectors:
            result = await detector(page)
            if result.present:
                return result
        return CaptchaResult(type="none", present=False)
